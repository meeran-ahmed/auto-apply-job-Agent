import time
import hashlib
from typing import Set, Dict
from loguru import logger
from selenium.webdriver.common.by import By


class LoopGuard:
    """
    Implements anti-loop guardrails based on `reticle` principles:
    - Tracks form state hashes to detect infinite cycling on Next/Review steps.
    - Limits repeated attempts on identical elements.
    - Enforces verified success confirmation.
    """

    def __init__(self, max_step_repeats: int = 3, max_total_steps: int = 12):
        self.max_step_repeats = max_step_repeats
        self.max_total_steps = max_total_steps
        self.step_history: Dict[str, int] = {}
        self.total_steps = 0

    def reset(self):
        self.step_history.clear()
        self.total_steps = 0

    def compute_state_hash(self, driver) -> str:
        """
        Creates a fast hash of the current interactive inputs & visible text on screen.
        """
        try:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            ids = [i.get_attribute("id") or i.get_attribute("name") or "" for i in inputs[:15]]
            url = driver.current_url
            raw = f"{url}|{''.join(ids)}"
            return hashlib.md5(raw.encode("utf-8")).hexdigest()
        except Exception:
            return str(time.time())

    def check_and_record(self, driver) -> bool:
        """
        Returns True if safe to proceed; False if an infinite loop or excessive cycling is detected.
        """
        self.total_steps += 1
        if self.total_steps > self.max_total_steps:
            logger.warning(f"[LoopGuard] Exceeded maximum allowed form steps ({self.max_total_steps}). Breaking loop.")
            return False

        state_hash = self.compute_state_hash(driver)
        count = self.step_history.get(state_hash, 0) + 1
        self.step_history[state_hash] = count

        if count > self.max_step_repeats:
            logger.warning(f"[LoopGuard] Infinite loop detected! State visited {count} times without forward progress. Aborting.")
            return False

        return True

    @staticmethod
    def verify_success(driver) -> bool:
        """
        Validates that an application genuinely completed with an explicit confirmation signal.
        """
        try:
            url = driver.current_url.lower()
            success_url_patterns = [
                "/confirmation", "/thanks", "/applied", "/success", 
                "applied=true", "status=submitted", "submission-received"
            ]
            if any(p in url for p in success_url_patterns):
                return True

            body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            confirmation_phrases = [
                "thank you for applying",
                "your application has been submitted",
                "application submitted",
                "we have received your application",
                "we've received your application",
                "application sent",
                "thanks for applying",
                "your application was sent"
            ]
            if any(phrase in body_text for phrase in confirmation_phrases):
                return True
        except Exception:
            pass
        return False
