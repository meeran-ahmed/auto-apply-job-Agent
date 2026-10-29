import time
import urllib.parse
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from src.core.stealth_driver import StealthDriver
from src.core.loop_guard import LoopGuard
from src.core.fit_evaluator import FitEvaluator
from src.core.reticle_verifier import ReticleVerifier
from src.agents.drafter_reviewer import DrafterReviewerEngine


class LinkedInAgent:
    """
    Next-Level LinkedIn Autonomous Application Agent.
    - Evaluates 100-point vacancy fit (Zero internships, zero seniors).
    - Uses Drafter-Reviewer two-agent engine for question answering.
    - Employs ReticleVerifier for strict inside-out terminal submission verification.
    """

    def __init__(self, driver, gemini_answerer=None, reporter=None):
        self.driver = driver
        self.gemini_answerer = gemini_answerer
        self.reporter = reporter
        self.loop_guard = LoopGuard()
        self.fit_evaluator = FitEvaluator()
        self.drafter_reviewer = DrafterReviewerEngine(gemini_answerer=gemini_answerer)
        self.reticle_verifier = ReticleVerifier()

    def search_and_apply(self, keyword: str = "Full Stack Developer", location: str = "Remote", max_jobs: int = 5) -> int:
        self._ensure_authenticated()

        encoded_kw = urllib.parse.quote(keyword)
        encoded_loc = urllib.parse.quote(location)
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_kw}&location={encoded_loc}&f_AL=true&f_WT=2&sortBy=DD"
        logger.info(f"[LinkedInAgent] Navigating to LinkedIn Remote Easy Apply search: {search_url}")

        self.driver.get(search_url)
        StealthDriver.random_sleep(4.0, 6.0)

    def _ensure_authenticated(self):
        """Injects li_at session cookie from secrets.yaml if present to bypass all login walls."""
        import yaml
        from pathlib import Path
        secrets_file = Path("data_folder/secrets.yaml")
        li_at_token = None
        if secrets_file.exists():
            try:
                with open(secrets_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    li_at_token = data.get("linkedin_li_at") or data.get("li_at")
            except Exception:
                pass

        if li_at_token:
            try:
                logger.info("[LinkedInAgent] Injecting authenticated li_at session cookie...")
                self.driver.get("https://www.linkedin.com")
                time.sleep(1.5)
                self.driver.add_cookie({
                    "name": "li_at",
                    "value": str(li_at_token).strip(),
                    "domain": ".linkedin.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True
                })
                self.driver.get("https://www.linkedin.com/feed/")
                time.sleep(2.5)
                logger.info(f"[LinkedInAgent] Authenticated session established! Current page: {self.driver.title}")
            except Exception as e:
                logger.warning(f"[LinkedInAgent] Error injecting li_at cookie: {e}")

        job_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/jobs/view/')]")
        logger.info(f"[LinkedInAgent] Found {len(job_links)} job links on page.")

        candidates = []
        for a in job_links:
            try:
                href = a.get_attribute("href")
                if not href:
                    continue
                clean_href = href.split("?")[0]
                title = a.text.strip().replace("\n", " ")

                if not title:
                    slug = clean_href.split("/view/")[-1]
                    title = slug.replace("-", " ").title()

                # Evaluate fit using 100-Point FitEvaluator
                score, is_fit, details = self.fit_evaluator.evaluate_fit(title, description="", location=location)
                if not is_fit:
                    continue

                if clean_href not in [c[0] for c in candidates]:
                    candidates.append((clean_href, title, score))
            except Exception as e:
                logger.debug(f"[LinkedInAgent] Error parsing job link: {e}")

        logger.info(f"[LinkedInAgent] Filtered {len(candidates)} verified target developer positions (Fit Score >= 75, no internships).")

        applied_count = 0
        for link, title, fit_score in candidates:
            if applied_count >= max_jobs:
                break

            if self.reporter and self.reporter.is_already_applied(link, title):
                logger.info(f"[LinkedInAgent] Already applied to '{title}', skipping...")
                continue

            try:
                verified, company, reason = self.apply_to_job(title, link)
                if verified:
                    applied_count += 1
                    logger.info(f"[LinkedInAgent] [VERIFIED SUBMISSION] Applied to '{title}' at '{company}' ({applied_count}/{max_jobs})")
                    if self.reporter:
                        self.reporter.record_applied(title, company, "LinkedIn", link)
                else:
                    logger.warning(f"[LinkedInAgent] [BLOCKED/UNVERIFIED] Could not verify terminal submission for '{title}' at '{company}' (Reason: {reason})")
                StealthDriver.random_sleep(4.0, 6.0)
            except Exception as e:
                logger.error(f"[LinkedInAgent] Error applying to '{title}': {e}")

        return applied_count

    def apply_to_job(self, title: str, link: str):
        logger.info(f"[LinkedInAgent] Opening job: '{title}' -> {link}")
        self.driver.get(link)
        StealthDriver.random_sleep(3.0, 5.0)

        # Extract company name
        company = "LinkedIn Hiring Employer"
        comp_elems = self.driver.find_elements(
            By.CSS_SELECTOR,
            "a.topcard__org-name-link, span.topcard__flavor, a[data-tracking-control-name*='company'], a[href*='/company/']"
        )
        if comp_elems and comp_elems[0].text.strip():
            company = comp_elems[0].text.strip().split("\n")[0]
        elif "-at-" in link:
            parts = link.split("-at-")[-1].split("-")
            if len(parts) >= 2:
                company = parts[0].capitalize()

        # Find Apply / Easy Apply button
        apply_buttons = self.driver.find_elements(
            By.XPATH,
            "//button[contains(@class, 'apply-button') or contains(., 'Easy Apply') or contains(., 'Apply')] | "
            "//a[contains(@class, 'apply-button') or contains(., 'Easy Apply') or contains(., 'Apply')]"
        )

        if not apply_buttons:
            logger.info(f"[LinkedInAgent] No active apply button found for '{title}' (may be closed or applied).")
            return False, company, "No apply button found"

        btn = apply_buttons[0]
        StealthDriver.human_click(self.driver, btn)
        StealthDriver.random_sleep(2.5, 4.0)

        # Handle external ATS redirect tabs: DO NOT fake-log success!
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[-1])
            StealthDriver.random_sleep(2.0, 3.5)
            external_url = self.driver.current_url
            logger.info(f"[LinkedInAgent] External career site redirect detected: {external_url}")
            # Close external tab and return False so it is not fake-logged
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            return False, company, f"Redirected to external ATS portal ({external_url})"

        # Process multi-step Easy Apply modal
        steps = 0
        while steps < 12:
            steps += 1

            # Reticle verification check at each step
            is_done, verdict, details = self.reticle_verifier.verify_terminal_submission(self.driver, company, title)
            if is_done:
                return True, company, "Terminal confirmation confirmed"

            self._fill_modal_fields(title, company)

            # Check for Submit application
            submit_btn = self.driver.find_elements(By.XPATH, "//button[contains(., 'Submit application') or contains(., 'Submit')]")
            if submit_btn and submit_btn[0].is_displayed():
                StealthDriver.human_click(self.driver, submit_btn[0])
                StealthDriver.random_sleep(3.5, 5.0)
                # Final Reticle verification after submit click
                is_done, verdict, details = self.reticle_verifier.verify_terminal_submission(self.driver, company, title)
                return is_done, company, details.get("reason", verdict)

            # Check for Review
            review_btn = self.driver.find_elements(By.XPATH, "//button[contains(., 'Review')]")
            if review_btn and review_btn[0].is_displayed():
                StealthDriver.human_click(self.driver, review_btn[0])
                StealthDriver.random_sleep(2.0, 3.0)
                continue

            # Check for Next
            next_btn = self.driver.find_elements(By.XPATH, "//button[contains(., 'Next')]")
            if next_btn and next_btn[0].is_displayed():
                StealthDriver.human_click(self.driver, next_btn[0])
                StealthDriver.random_sleep(2.0, 3.0)
                continue

            # If no progression button is displayed, stop loop
            break

        # Final verification check before declaring outcome
        is_done, verdict, details = self.reticle_verifier.verify_terminal_submission(self.driver, company, title)
        return is_done, company, details.get("reason", "Incomplete Easy Apply modal steps")

    def _fill_modal_fields(self, job_title: str, company: str):
        """Fills visible text inputs, textareas, and radio buttons using DrafterReviewer."""
        try:
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='modal'] input[type='text'], div[class*='modal'] textarea")
            for inp in inputs:
                if inp.is_displayed() and not inp.get_attribute("value"):
                    label = inp.get_attribute("aria-label") or inp.get_attribute("placeholder") or "Experience"
                    answer = self.drafter_reviewer.generate_verified_answer(label, job_title, company)
                    StealthDriver.human_type(inp, answer)
                    time.sleep(0.3)

            # Work authorization / Yes radio buttons
            radios = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='modal'] input[type='radio'][value='Yes'], div[class*='modal'] input[type='radio'][value='yes']")
            for r in radios:
                if r.is_displayed() and not r.is_selected():
                    StealthDriver.human_click(self.driver, r)
        except Exception as e:
            logger.debug(f"[LinkedInAgent] Modal field note: {e}")
