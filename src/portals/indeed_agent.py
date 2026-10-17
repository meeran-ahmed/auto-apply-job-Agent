import time
import urllib.parse
from loguru import logger
from selenium.webdriver.common.by import By
from src.core.stealth_driver import StealthDriver
from src.core.loop_guard import LoopGuard


class IndeedAgent:
    """
    Automates applications on Indeed.com targeting remote developer roles
    with 1-click Indeed Apply using the user's active Chrome session.
    """

    def __init__(self, driver, gemini_answerer=None, reporter=None):
        self.driver = driver
        self.gemini_answerer = gemini_answerer
        self.reporter = reporter
        self.loop_guard = LoopGuard()

    def search_and_apply(self, keyword: str = "Full Stack Developer", location: str = "Remote", max_jobs: int = 10) -> int:
        encoded_kw = urllib.parse.quote(keyword)
        encoded_loc = urllib.parse.quote(location)
        search_url = f"https://www.indeed.com/jobs?q={encoded_kw}&l={encoded_loc}&fromage=3&iafilter=1"
        logger.info(f"[IndeedAgent] Navigating to Indeed search: {search_url}")

        self.driver.get(search_url)
        StealthDriver.random_sleep(3.5, 5.5)

        cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon, td.resultContent, a.jcs-JobTitle")
        logger.info(f"[IndeedAgent] Found {len(cards)} job listings on page.")

        links = []
        for card in cards:
            try:
                a_tag = card if card.tag_name == "a" else card.find_element(By.CSS_SELECTOR, "a.jcs-JobTitle, a[id^='job_']")
                href = a_tag.get_attribute("href")
                title = a_tag.text.strip()
                if href and self._is_target_role(title):
                    links.append((title, href))
            except Exception:
                continue

        # Deduplicate links while maintaining order
        links = list(dict.fromkeys(links))
        logger.info(f"[IndeedAgent] Filtered {len(links)} matching candidate roles with Indeed Apply.")
        applied_count = 0

        for title, link in links:
            if applied_count >= max_jobs:
                break
            try:
                success = self.apply_to_job(title, link)
                if success:
                    applied_count += 1
                    logger.info(f"[IndeedAgent] Successfully applied to '{title}' on Indeed ({applied_count}/{max_jobs})")
                    if self.reporter:
                        self.reporter.record_applied(title, "Indeed Hiring Employer", "Indeed", link)
                StealthDriver.random_sleep(3.0, 5.0)
            except Exception as e:
                logger.error(f"[IndeedAgent] Error applying to {title}: {e}")

        return applied_count

    def apply_to_job(self, title: str, link: str) -> bool:
        logger.info(f"[IndeedAgent] Opening job: {title} -> {link}")
        self.driver.get(link)
        StealthDriver.random_sleep(2.5, 4.0)

        apply_btn = self.driver.find_elements(
            By.XPATH,
            "//button[contains(., 'Apply now') or contains(., 'Indeed Apply') or contains(@id, 'indeedApplyButton')] | "
            "//a[contains(., 'Apply now') or contains(., 'Indeed Apply')]"
        )

        if not apply_btn:
            logger.info(f"[IndeedAgent] Job '{title}' does not have 1-click Indeed Apply or already applied.")
            return False

        StealthDriver.human_click(self.driver, apply_btn[0])
        StealthDriver.random_sleep(2.5, 4.0)

        # Multi-step Indeed modal navigation
        self.loop_guard.reset()
        for _ in range(8):
            if not self.loop_guard.check_and_record(self.driver):
                break

            # Answer any visible questions
            self._fill_step_fields(title)

            # Look for Continue or Submit button
            continue_btn = self.driver.find_elements(
                By.XPATH,
                "//button[contains(., 'Submit your application') or contains(., 'Submit') or contains(., 'Review your application') or contains(., 'Continue')] | "
                "//button[contains(@class, 'ia-continueButton') or contains(@class, 'ia-SubmitButton')]"
            )
            if not continue_btn:
                break

            btn_text = continue_btn[0].text.lower()
            is_final_submit = "submit" in btn_text

            StealthDriver.human_click(self.driver, continue_btn[0])
            StealthDriver.random_sleep(2.0, 3.5)

            if is_final_submit or LoopGuard.verify_success(self.driver):
                logger.info(f"[IndeedAgent] Confirmation verified for '{title}'!")
                return True

        return LoopGuard.verify_success(self.driver)

    def _fill_step_fields(self, job_title: str):
        inputs = self.driver.find_elements(By.XPATH, "//input[@type='text' and not(@value)] | //textarea[not(text())]")
        for inp in inputs:
            try:
                if inp.is_displayed():
                    label = inp.get_attribute("aria-label") or inp.get_attribute("placeholder") or "Experience"
                    answer = self.gemini_answerer.answer_question(label, job_title=job_title) if self.gemini_answerer else "Yes, 3 years"
                    StealthDriver.human_type(inp, answer)
                    time.sleep(0.3)
            except Exception:
                pass

    def _is_target_role(self, title: str) -> bool:
        t = title.lower()
        blacklist = ["intern", "internship", "senior", "sr.", "lead", "architect", "manager", "director", "head", "trainee"]
        if any(b in t for b in blacklist):
            return False
        keywords = ["developer", "engineer", "full stack", "frontend", "python", "react", "web", "software"]
        return any(k in t for k in keywords)
