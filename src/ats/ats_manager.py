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

        # Direct targeted engine attempt
        if ats_type == "greenhouse":
            if self.greenhouse.apply(job_title, company):
                return True
        elif ats_type == "lever":
            if self.lever.apply(job_title, company):
                return True
        elif ats_type == "ashby":
            if self.ashby.apply(job_title, company):
                return True

        # Multi-engine universal fallback
        logger.info(f"Applying via Universal ATS engine fallback for: {current_url}")
        for engine_name, engine in [("Greenhouse/Universal", self.greenhouse), ("Lever", self.lever), ("Ashby", self.ashby)]:
            try:
                logger.debug(f"Attempting {engine_name} engine...")
                if engine.apply(job_title, company):
                    logger.info(f"Successfully submitted application using {engine_name} engine!")
                    return True
            except Exception as e:
                logger.debug(f"{engine_name} attempt note: {e}")
                continue

        logger.warning(f"Could not auto-submit form for {current_url}")
        return False
