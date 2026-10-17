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

            # Check if this is an external job board with an intermediary "Apply" button
            current_target = self.driver.current_url.lower()
            is_direct_ats = any(k in current_target for k in ["/jobs/", "job-boards.greenhouse.io", "boards.greenhouse.io", "jobs.lever.co", "jobs.ashbyhq.com", "myworkdayjobs.com", "smartrecruiters.com"]) and not any(portal in current_target for portal in ["jobicy.com", "weworkremotely.com", "arbeitnow.com", "himalayas.app", "remoteok.com"])

            if not is_direct_ats:
                try:
                    apply_elements = self.driver.find_elements(
                        "xpath",
                        "//a[contains(@href, 'greenhouse') or contains(@href, 'lever') or contains(@href, 'ashby') or contains(@href, 'workday') or contains(@href, 'smartrecruiters') or contains(@href, 'recruitee') or contains(@href, 'workable') or contains(@href, 'bamboohr') or contains(@href, 'rippling') or contains(@href, 'external')] | "
                        "//a[contains(translate(., 'APPLY', 'apply'), 'apply') and not(contains(@href, 'mailto:')) and not(contains(@href, '#')) and not(contains(@href, 'ai-copilot'))] | "
                        "//button[contains(translate(., 'APPLY', 'apply'), 'apply')] | "
                        "//a[contains(@class, 'apply') or contains(@id, 'apply')]"
                    )
                    if apply_elements:
                        for btn in apply_elements:
                            dest_href = btn.get_attribute("href")
                            if dest_href and dest_href.startswith("http") and not any(board in dest_href for board in ["remoterocketship.com", "jobicy.com/jobs", "weworkremotely.com/categories"]):
                                logger.info(f"[ATSAgent] Navigating directly to external ATS link: {dest_href}")
                                self.driver.get(dest_href)
                                time.sleep(3.5)
                                break
                            else:
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                                time.sleep(1)
                                self.driver.execute_script("arguments[0].click();", btn)
                                time.sleep(3.5)
                                break
                        
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
