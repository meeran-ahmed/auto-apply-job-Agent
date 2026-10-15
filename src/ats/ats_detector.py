import re
from loguru import logger
from selenium.webdriver.common.by import By


class ATSDetector:
    """
    Detects which Applicant Tracking System (ATS) or career page format is being used.
    """

    @staticmethod
    def detect(driver, url: str) -> str:
        url_lower = (url or "").lower()

        # 1. Direct URL pattern detection
        if "greenhouse.io" in url_lower or "grnh.se" in url_lower:
            logger.info("Detected ATS: Greenhouse")
            return "greenhouse"

        if "jobs.lever.co" in url_lower or "lever.co" in url_lower:
            logger.info("Detected ATS: Lever")
            return "lever"

        if "ashbyhq.com" in url_lower:
            logger.info("Detected ATS: Ashby")
            return "ashby"

        if "myworkdayjobs.com" in url_lower or "workday.com" in url_lower:
            logger.info("Detected ATS: Workday")
            return "workday"

        if "smartrecruiters.com" in url_lower:
            logger.info("Detected ATS: SmartRecruiters")
            return "smartrecruiters"

        if any(ats in url_lower for ats in ["recruitee.com", "workable.com", "bamboohr.com", "rippling.com", "pinpointhq.com"]):
            logger.info("Detected ATS: Standard ATS Platform")
            return "generic"

        # 2. DOM inspection detection (for white-labeled custom domains)
        try:
            page_source = driver.page_source.lower()
            if "greenhouse" in page_source or driver.find_elements(By.CSS_SELECTOR, "form#application_form, #grnhse_app"):
                logger.info("Detected ATS: Greenhouse (embedded)")
                return "greenhouse"

            if "lever.co" in page_source or driver.find_elements(By.CSS_SELECTOR, ".lever-application-form, form[action*='lever.co']"):
                logger.info("Detected ATS: Lever (embedded)")
                return "lever"

            if "ashby" in page_source or driver.find_elements(By.CSS_SELECTOR, "[data-ashby-application-form]"):
                logger.info("Detected ATS: Ashby (embedded)")
                return "ashby"

            # Check if there is an application form with a file input (resume)
            file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            text_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email']")
            if file_inputs and len(text_inputs) >= 2:
                logger.info("Detected ATS: Generic Universal Application Form")
                return "generic"
        except Exception as e:
            logger.debug(f"ATS DOM detection note: {e}")

        return "unknown"
