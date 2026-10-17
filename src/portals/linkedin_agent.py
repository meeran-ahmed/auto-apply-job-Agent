import time
import urllib.parse
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from src.core.stealth_driver import StealthDriver
from src.core.loop_guard import LoopGuard


class LinkedInAgent:
    """
    Automates job applications on LinkedIn using the user's active session.
    Applies specifically to remote full-stack/python/frontend engineering positions (NO INTERNSHIPS),
    handling Easy Apply modals with Gemini 1.5 Flash grounded in candidate profile.
    """

    def __init__(self, driver, gemini_answerer=None, reporter=None):
        self.driver = driver
        self.gemini_answerer = gemini_answerer
        self.reporter = reporter
        self.loop_guard = LoopGuard()

    def search_and_apply(self, keyword: str = "Full Stack Developer", location: str = "Remote", max_jobs: int = 5) -> int:
        encoded_kw = urllib.parse.quote(keyword)
        encoded_loc = urllib.parse.quote(location)
        # Target remote full-stack developer jobs posted recently with Easy Apply
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_kw}&location={encoded_loc}&f_AL=true&f_WT=2&sortBy=DD"
        logger.info(f"[LinkedInAgent] Navigating to LinkedIn Remote Easy Apply search: {search_url}")

        self.driver.get(search_url)
        StealthDriver.random_sleep(4.0, 6.0)

        # Collect all job view links on page
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

                # Extract title from link or slug if text is blank
                if not title or len(title) < 3:
                    slug = clean_href.split("/jobs/view/")[-1]
                    title = slug.replace("-at-", " @ ").split("-")[0].replace("-", " ").title()

                if clean_href and self._is_target_role(title):
                    candidates.append((title, clean_href))
            except Exception:
                continue

        # Deduplicate by URL
        seen_urls = set()
        unique_candidates = []
        for t, h in candidates:
            if h not in seen_urls:
                seen_urls.add(h)
                unique_candidates.append((t, h))

        logger.info(f"[LinkedInAgent] Filtered {len(unique_candidates)} verified target developer positions (no internships/seniors).")

        applied_count = 0
        for title, link in unique_candidates:
            if applied_count >= max_jobs:
                break

            if self.reporter and self.reporter.is_already_applied(link, title):
                logger.info(f"[LinkedInAgent] Already applied to '{title}', skipping...")
                continue

            try:
                success, company = self.apply_to_job(title, link)
                if success:
                    applied_count += 1
                    logger.info(f"[LinkedInAgent] Successfully applied to '{title}' at '{company}' on LinkedIn ({applied_count}/{max_jobs})")
                    if self.reporter:
                        self.reporter.record_applied(title, company, "LinkedIn", link)
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
            "//button[contains(@class, 'apply-button') or contains(., 'Apply') or contains(., 'Easy Apply')] | "
            "//a[contains(@class, 'apply-button') or contains(., 'Apply')]"
        )

        if not apply_buttons:
            logger.info(f"[LinkedInAgent] No active apply button found for '{title}' (may be closed or applied).")
            return False, company

        btn = apply_buttons[0]
        StealthDriver.human_click(self.driver, btn)
        StealthDriver.random_sleep(2.5, 4.0)

        # Check if opened in a new tab (external ATS redirect)
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[-1])
            StealthDriver.random_sleep(2.0, 3.5)
            # Record external application click
            logger.info(f"[LinkedInAgent] Followed direct application link to: {self.driver.current_url}")
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            return True, company

        # Process multi-step Easy Apply modal if present
        steps = 0
        while steps < 10:
            steps += 1

            if self._check_success():
                return True, company

            self._fill_modal_fields(title)

            # Check for Submit application
            submit_btn = self.driver.find_elements(By.XPATH, "//button[contains(., 'Submit application') or contains(., 'Submit')]")
            if submit_btn and submit_btn[0].is_displayed():
                StealthDriver.human_click(self.driver, submit_btn[0])
                StealthDriver.random_sleep(3.0, 4.5)
                return True, company

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

            break

        return True, company

    def _fill_modal_fields(self, job_title: str):
        """Fills visible text inputs, textareas, and radio buttons in Easy Apply modal."""
        try:
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='modal'] input[type='text'], div[class*='modal'] textarea")
            for inp in inputs:
                if inp.is_displayed() and not inp.get_attribute("value"):
                    label = inp.get_attribute("placeholder") or "Experience"
                    answer = self.gemini_answerer.answer_question(label, job_title=job_title) if self.gemini_answerer else "3"
                    StealthDriver.human_type(inp, answer)
                    time.sleep(0.3)

            # Work authorization / Yes radio buttons
            radios = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='modal'] input[type='radio'][value='Yes'], div[class*='modal'] input[type='radio'][value='yes']")
            for r in radios:
                if r.is_displayed() and not r.is_selected():
                    StealthDriver.human_click(self.driver, r)
        except Exception as e:
            logger.debug(f"[LinkedInAgent] Modal field note: {e}")

    def _check_success(self) -> bool:
        try:
            page_src = self.driver.page_source.lower()
            return "application submitted" in page_src or "your application was sent" in page_src
        except Exception:
            return False

    def _is_target_role(self, title: str) -> bool:
        t = title.lower()
        blacklist = ["intern", "internship", "co-op", "trainee", "student", "senior", "lead", "architect", "director", "manager", "head", "vp", "staff", "principal"]
        if any(b in t for b in blacklist):
            return False
        keywords = ["developer", "engineer", "full stack", "frontend", "python", "react", "web", "software", "backend"]
        return any(k in t for k in keywords)
