import time
from loguru import logger
from selenium.webdriver.common.by import By
from src.core.stealth_driver import StealthDriver
from src.core.loop_guard import LoopGuard


class CutshortAgent:
    """
    Automates applications on Cutshort (India's leading tech startup matching platform)
    using the user's active Chrome session.
    """

    def __init__(self, driver, gemini_answerer=None, reporter=None):
        self.driver = driver
        self.gemini_answerer = gemini_answerer
        self.reporter = reporter

    def search_and_apply(self, keyword: str = "full stack developer", max_jobs: int = 10) -> int:
        search_url = "https://cutshort.io/jobs?remote=true"
        logger.info(f"[CutshortAgent] Navigating to Cutshort startup jobs: {search_url}")

        self.driver.get(search_url)
        StealthDriver.random_sleep(4.0, 6.0)

        job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='job-card'], div[class*='JobCard'], a[href*='/job/']")
        logger.info(f"[CutshortAgent] Found {len(job_cards)} startup job cards.")

        applied_count = 0
        for card in job_cards[:max_jobs * 2]:
            if applied_count >= max_jobs:
                break
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, "h2, h3, a[href*='/job/']")
                title = title_elem.text.strip()
                if not self._is_target_role(title):
                    continue

                apply_btn = card.find_elements(By.XPATH, ".//button[contains(., 'Apply') or contains(., 'Interested')]")
                if apply_btn:
                    StealthDriver.human_click(self.driver, apply_btn[0])
                    StealthDriver.random_sleep(2.0, 3.5)
                    applied_count += 1
                    logger.info(f"[CutshortAgent] Applied to startup role: '{title}' ({applied_count}/{max_jobs})")
                    if self.reporter:
                        self.reporter.record_applied(title, "Cutshort Startup", "Cutshort", self.driver.current_url)
            except Exception as e:
                logger.debug(f"[CutshortAgent] Card processing note: {e}")

        return applied_count

    def _is_target_role(self, title: str) -> bool:
        t = title.lower()
        blacklist = ["intern", "internship", "senior", "lead", "architect", "manager", "head"]
        if any(b in t for b in blacklist):
            return False
        keywords = ["developer", "engineer", "full stack", "frontend", "python", "react", "web", "software"]
        return any(k in t for k in keywords)
