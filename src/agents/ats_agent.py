import time
from loguru import logger
from src.ats.ats_manager import ATSManager


class ATSAgent:
    """
    Dedicated worker agent for applying to external ATS systems
    (Greenhouse, Lever, Ashby, Workday, and company career portals).
    """

    def __init__(self, driver, resume_path: str, profile_data: dict, gpt_answerer=None, reporter=None):
        self.driver = driver
        self.resume_path = resume_path
        self.profile_data = profile_data
        self.gpt_answerer = gpt_answerer
        self.reporter = reporter
        self.ats_manager = ATSManager(driver, resume_path, profile_data, gpt_answerer)

    def process_job(self, job: dict) -> bool:
        title = job.get("title", "")
        company = job.get("company", "")
        url = job.get("url", "")
        platform = job.get("platform", "ATS Portal")

        logger.info(f"[ATSAgent] Navigating to: '{title}' at '{company}' -> {url}")
        try:
            self.driver.get(url)
            time.sleep(3)

            # Check if there is an intermediary "Apply" button or link
            try:
                apply_elements = self.driver.find_elements(
                    "xpath",
                    "//a[contains(@href, 'greenhouse') or contains(@href, 'lever') or contains(@href, 'ashby') or contains(@href, 'workday') or contains(@href, 'smartrecruiters') or contains(@href, 'external')] | "
                    "//a[contains(translate(., 'APPLY', 'apply'), 'apply') and not(contains(@href, 'mailto:')) and not(contains(@href, '#'))] | "
                    "//button[contains(translate(., 'APPLY', 'apply'), 'apply')] | "
                    "//a[contains(@class, 'apply') or contains(@id, 'apply')]"
                )
                if apply_elements:
                    btn = apply_elements[0]
                    dest_href = btn.get_attribute("href")
                    if dest_href and dest_href.startswith("http") and ("jobicy.com" not in dest_href or "external" in dest_href):
                        logger.info(f"[ATSAgent] Navigating directly to external ATS link: {dest_href}")
                        self.driver.get(dest_href)
                        time.sleep(3.5)
                    else:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        time.sleep(1)
                        self.driver.execute_script("arguments[0].click();", btn)
                        time.sleep(3.5)
                    
                    if len(self.driver.window_handles) > 1:
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        logger.info(f"[ATSAgent] Switched to new window handle: {self.driver.current_url}")
            except Exception as e:
                logger.debug(f"Intermediary apply link error: {e}")

            success = self.ats_manager.apply_to_external_page(title, company)
            if success:
                logger.info(f"[ATSAgent] SUCCESS: Applied to '{title}' at '{company}'!")
                if self.reporter:
                    self.reporter.record_applied(title, company, platform, url)
                return True
            else:
                logger.warning(f"[ATSAgent] Could not auto-submit form for '{title}' at '{company}'.")
                if self.reporter:
                    self.reporter.record_skipped(title, company, "Form required unsupported custom verification")
                return False

        except Exception as e:
            logger.error(f"[ATSAgent] Error applying to {url}: {e}")
            if self.reporter:
                self.reporter.record_failed(title, company, str(e))
            return False
