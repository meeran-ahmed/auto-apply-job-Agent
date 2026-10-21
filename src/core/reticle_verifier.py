import time
import requests
from typing import Dict, Any, Tuple
from loguru import logger
from selenium.webdriver.common.by import By

class ReticleVerifier:
    """
    Reticle Inside-Out Submission Verification Layer (v3.7.0).
    Eliminates loop mistakes and false-positive application logging by
    strictly asserting that terminal confirmation states are reached.
    """

    def __init__(self, daemon_url: str = "http://localhost:4400"):
        self.daemon_url = daemon_url
        self.success_phrases = [
            "application submitted",
            "your application was sent",
            "thank you for applying",
            "application received",
            "we have received your application",
            "successfully submitted",
            "candidature envoyée",
            "postuler envoyé"
        ]

    def verify_terminal_submission(self, driver, company: str, job_title: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Inspects the live browser DOM to compute an absolute verdict:
        - PASS: 'yes' (Terminal submission element is visible and confirmed)
        - FAIL: 'no' (Login wall, required field missing, or error detected)
        - UNKNOWN: 'unknown' (Page hung or unrecognised state)
        """
        evidence = {}
        time.sleep(2.0) # Settle time for network responses

        try:
            current_url = driver.current_url.lower()
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            evidence["url"] = current_url

            # 1. Check for genuine success confirmation phrases
            for phrase in self.success_phrases:
                if phrase in page_text:
                    logger.info(f"[ReticleVerifier] VERIFIED 'yes': Found terminal confirmation phrase '{phrase}' for '{job_title}' at '{company}'")
                    return True, "yes", {"verdict": "yes", "confirmed_phrase": phrase, "url": current_url}

            # 2. Check for URL redirect to thank-you / confirmation page
            if any(term in current_url for term in ["/thank-you", "/thanks", "/confirmation", "/applied", "status=success"]):
                logger.info(f"[ReticleVerifier] VERIFIED 'yes': Terminal success URL reached: {current_url}")
                return True, "yes", {"verdict": "yes", "confirmed_url": current_url}

            # 3. Check for blocker indicators (Login walls, reCAPTCHA, unselected required fields)
            if "sign in to apply" in page_text or "join linkedin" in page_text or "login to apply" in page_text:
                logger.warning(f"[ReticleVerifier] VERIFIED 'no': Application blocked by login wall on {current_url}")
                return False, "no", {"verdict": "no", "reason": "Login wall or unauthenticated session", "url": current_url}

            if "please enter a valid" in page_text or "field is required" in page_text or "required file missing" in page_text:
                logger.warning(f"[ReticleVerifier] VERIFIED 'no': Form validation error detected")
                return False, "no", {"verdict": "no", "reason": "Missing required field or validation error", "url": current_url}

            # 4. If neither success nor explicit blocker found, verdict is 'unknown'
            logger.warning(f"[ReticleVerifier] VERIFIED 'unknown': No terminal confirmation detected on page for '{job_title}'")
            return False, "unknown", {"verdict": "unknown", "reason": "No terminal confirmation element found", "url": current_url}

        except Exception as e:
            logger.error(f"[ReticleVerifier] Verification exception: {e}")
            return False, "unknown", {"verdict": "unknown", "error": str(e)}

    def check_daemon_health(self) -> bool:
        """
        Verifies if Reticle daemon is active on localhost:4400.
        """
        try:
            resp = requests.get(f"{self.daemon_url}/health", timeout=1.0)
            return resp.status_code == 200
        except Exception:
            return False
