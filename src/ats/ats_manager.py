from loguru import logger
from src.ats.ats_detector import ATSDetector
from src.ats.greenhouse_applier import GreenhouseApplier
from src.ats.lever_applier import LeverApplier
from src.ats.ashby_applier import AshbyApplier


class ATSManager:
    """
    Coordinates detection and autonomous submission for external ATS career pages.
    """

    def __init__(self, driver, resume_path: str, profile_data: dict, gpt_answerer=None):
        self.driver = driver
        self.resume_path = resume_path
        self.profile_data = profile_data
        self.gpt_answerer = gpt_answerer

        self.greenhouse = GreenhouseApplier(driver, resume_path, profile_data, gpt_answerer)
        self.lever = LeverApplier(driver, resume_path, profile_data, gpt_answerer)
        self.ashby = AshbyApplier(driver, resume_path, profile_data, gpt_answerer)

    def apply_to_external_page(self, job_title: str = "", company: str = "") -> bool:
        current_url = self.driver.current_url
        ats_type = ATSDetector.detect(self.driver, current_url)
        logger.info(f"Target URL: {current_url} -> Detected ATS: {ats_type}")

        if ats_type == "greenhouse":
            return self.greenhouse.apply(job_title, company)

        if ats_type == "lever":
            return self.lever.apply(job_title, company)

        if ats_type == "ashby":
            return self.ashby.apply(job_title, company)

        if ats_type == "generic":
            # Try greenhouse or lever form matching
            logger.info("Applying via Generic ATS strategy...")
            return self.greenhouse.apply(job_title, company) or self.lever.apply(job_title, company)

        logger.warning(f"Unsupported or unknown ATS for {current_url}")
        return False
