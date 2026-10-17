import time
import urllib.parse
from loguru import logger
from selenium.webdriver.common.by import By
from src.core.stealth_driver import StealthDriver
from src.core.loop_guard import LoopGuard


class InternshalaJobsAgent:
    """
    Automates applications strictly on Internshala's FULL-TIME JOBS portal
    (https://internshala.com/jobs/) - STRICTLY EXCLUDING INTERNSHIPS as requested by the user.
    """

    def __init__(self, driver, gemini_answerer=None, reporter=None):
        self.driver = driver
        self.gemini_answerer = gemini_answerer
        self.reporter = reporter
        self.loop_guard = LoopGuard()

    def search_and_apply(self, keyword: str = "web-development", max_jobs: int = 10) -> int:
        # Strictly target /jobs/ section (NOT /internships/)
        search_url = f"https://internshala.com/jobs/{keyword}-jobs/"
        logger.info(f"[InternshalaJobsAgent] Navigating strictly to FULL-TIME JOBS portal: {search_url}")

        self.driver.get(search_url)
        StealthDriver.random_sleep(3.5, 5.0)

        # Ensure we are not on internships page
        if "/internships" in self.driver.current_url:
            logger.warning("[InternshalaJobsAgent] Redirected to internships page. Re-routing back to /jobs/...")
            self.driver.get("https://internshala.com/jobs/")
            StealthDriver.random_sleep(3.0, 4.0)

        job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.individual_internship, div.job-card, div.container-fluid")
        logger.info(f"[InternshalaJobsAgent] Discovered {len(job_cards)} full-time job cards.")

        applied_count = 0
        links = []

        for card in job_cards:
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, "div.job-title, a.job-title-href, h3.job-internship-name")
                title = title_elem.text.strip()
                link = card.get_attribute("data-href") or title_elem.get_attribute("href")
                if link and not link.startswith("http"):
                    link = "https://internshala.com" + link

                if link and self._is_target_job(title):
                    links.append((title, link))
            except Exception:
                continue

        logger.info(f"[InternshalaJobsAgent] Filtered {len(links)} verified full-time developer jobs.")

        for title, link in links:
            if applied_count >= max_jobs:
                break
            try:
                success = self.apply_to_job(title, link)
                if success:
                    applied_count += 1
                    logger.info(f"[InternshalaJobsAgent] Applied to full-time job: '{title}' ({applied_count}/{max_jobs})")
                    if self.reporter:
                        self.reporter.record_applied(title, "Internshala Partner", "Internshala (Full-Time)", link)
                StealthDriver.random_sleep(3.0, 5.0)
            except Exception as e:
                logger.error(f"[InternshalaJobsAgent] Error applying to {title}: {e}")

        return applied_count

    def apply_to_job(self, title: str, link: str) -> bool:
        logger.info(f"[InternshalaJobsAgent] Opening job: {title} -> {link}")
        self.driver.get(link)
        StealthDriver.random_sleep(2.5, 4.0)

        apply_btn = self.driver.find_elements(By.CSS_SELECTOR, "button#apply_now_button, a#apply_now_button, button.btn-primary")
        if not apply_btn:
            logger.info(f"[InternshalaJobsAgent] Job '{title}' already applied or closed.")
            return False

        StealthDriver.human_click(self.driver, apply_btn[0])
        StealthDriver.random_sleep(2.0, 3.5)

        # Handle assessment questions
        textareas = self.driver.find_elements(By.CSS_SELECTOR, "textarea[name^='text_'], textarea.form-control")
        for ta in textareas:
            try:
                if ta.is_displayed():
                    label = ta.get_attribute("placeholder") or "Why should you be hired?"
                    answer = self.gemini_answerer.answer_question(label, job_title=title) if self.gemini_answerer else "I have hands-on experience building full-stack web applications with React and Python."
                    StealthDriver.human_type(ta, answer)
                    time.sleep(0.5)
            except Exception:
                pass

        submit_btn = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit']#submit, button#submit, input[value='Submit']")
        if submit_btn:
            StealthDriver.human_click(self.driver, submit_btn[0])
            StealthDriver.random_sleep(3.0, 4.5)
            return True

        return False

    def _is_target_job(self, title: str) -> bool:
        t = title.lower()
        # Strictly reject internships
        if any(term in t for term in ["intern", "internship", "stipend", "trainee", "senior", "lead", "architect"]):
            return False
        keywords = ["developer", "engineer", "full stack", "frontend", "python", "react", "web", "software"]
        return any(k in t for k in keywords)
