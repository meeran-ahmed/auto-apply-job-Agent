import time
from loguru import logger
from selenium.webdriver.common.by import By
from src.core.stealth_driver import StealthDriver
from src.core.loop_guard import LoopGuard


class WellfoundAgent:
    """
    Automates applications on Wellfound (formerly AngelList Talent),
    the world's premier startup job platform, using the user's active Chrome session.
    """

    def __init__(self, driver, gemini_answerer=None, reporter=None):
        self.driver = driver
        self.gemini_answerer = gemini_answerer
        self.reporter = reporter
        self.loop_guard = LoopGuard()

    def search_and_apply(self, keyword: str = "full stack developer", max_jobs: int = 10) -> int:
        search_url = "https://wellfound.com/jobs?remote=true"
        logger.info(f"[WellfoundAgent] Navigating to Wellfound remote startup jobs: {search_url}")

        self.driver.get(search_url)
        StealthDriver.random_sleep(4.0, 6.0)

        job_cards = self.driver.find_elements(
            By.CSS_SELECTOR,
            "div[data-test='JobListing'], div[class*='styles_jobListing'], div[class*='jobCard'], div[class*='styles_result']"
        )
        logger.info(f"[WellfoundAgent] Discovered {len(job_cards)} startup job cards.")

        applied_count = 0
        for card in job_cards[:max_jobs * 2]:
            if applied_count >= max_jobs:
                break
            try:
                title_elems = card.find_elements(By.CSS_SELECTOR, "a[data-test='JobTitle'], h4, h3, a[href*='/jobs/']")
                if not title_elems:
                    continue
                title = title_elems[0].text.strip()

                if not self._is_target_role(title):
                    continue

                company_elems = card.find_elements(By.CSS_SELECTOR, "h2, a[data-test='StartupName'], div[class*='startupName']")
                company = company_elems[0].text.strip() if company_elems else "Wellfound Startup"

                apply_btn = card.find_elements(By.XPATH, ".//button[contains(., 'Apply') or contains(., 'Quick Apply')]")
                if apply_btn:
                    StealthDriver.human_click(self.driver, apply_btn[0])
                    StealthDriver.random_sleep(2.5, 4.0)

                    # Check for application note / pitch modal
                    self._fill_application_modal(company, title)

                    applied_count += 1
                    logger.info(f"[WellfoundAgent] Submitted application to {company} - '{title}' ({applied_count}/{max_jobs})")
                    if self.reporter:
                        self.reporter.record_applied(title, company, "Wellfound", self.driver.current_url)

                    StealthDriver.random_sleep(3.0, 5.0)
            except Exception as e:
                logger.debug(f"[WellfoundAgent] Card note: {e}")

        return applied_count

    def _fill_application_modal(self, company: str, title: str):
        """Fills out candidate note if present and submits the modal."""
        try:
            # Check for note textarea
            textareas = self.driver.find_elements(
                By.CSS_SELECTOR,
                "textarea[placeholder*='note'], textarea[name*='note'], textarea[id*='note'], textarea"
            )
            for ta in textareas:
                if ta.is_displayed():
                    pitch = (
                        f"Hi {company} team,\n\n"
                        f"I'm excited to apply for the {title} role. As a Full Stack Developer experienced with "
                        f"React, TypeScript, Python, FastAPI, and PostgreSQL, I specialize in building fast, scalable web apps. "
                        f"You can explore my interactive projects at https://meeran-portfolio.antideploy.app.\n\n"
                        f"Looking forward to discussing how I can contribute to your team!\n"
                        f"Best regards,\nMeeran Ahmed R"
                    )
                    StealthDriver.human_type(ta, pitch)
                    StealthDriver.random_sleep(1.0, 2.0)
                    break

            # Click final Submit / Send Application button
            submit_buttons = self.driver.find_elements(
                By.XPATH,
                "//button[contains(., 'Send Application') or contains(., 'Submit') or contains(., 'Send')]"
            )
            for btn in submit_buttons:
                if btn.is_displayed():
                    StealthDriver.human_click(self.driver, btn)
                    StealthDriver.random_sleep(2.0, 3.5)
                    break
        except Exception as e:
            logger.debug(f"[WellfoundAgent] Modal fill note: {e}")

    def _is_target_role(self, title: str) -> bool:
        t = title.lower()
        blacklist = ["intern", "internship", "co-op", "trainee", "senior", "lead", "architect", "manager", "head"]
        if any(b in t for b in blacklist):
            return False
        keywords = ["developer", "engineer", "full stack", "frontend", "python", "react", "web", "software", "backend"]
        return any(k in t for k in keywords)
