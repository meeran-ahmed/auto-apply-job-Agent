import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from loguru import logger


class StealthDriver:
    """
    Implements anti-detection patterns from `invisible_dots`:
    - Masks automated navigator properties (webdriver, permissions).
    - Human-like typing with variable keystroke jitter.
    - Realistic smooth scrolling and mouse movement.
    """

    @staticmethod
    def apply_cdp_evasions(driver):
        """
        Injects stealth scripts via CDP before navigation.
        """
        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        window.navigator.chrome = {
                            runtime: {},
                            loadTimes: function() {},
                            csi: function() {},
                            app: {}
                        };
                        const originalQuery = window.navigator.permissions.query;
                        window.navigator.permissions.query = (parameters) => (
                            parameters.name === 'notifications' ?
                                Promise.resolve({ state: Notification.permission }) :
                                originalQuery(parameters)
                        );
                    """
                }
            )
            logger.debug("[StealthDriver] CDP anti-detection evasions injected successfully.")
        except Exception as e:
            logger.debug(f"[StealthDriver] Note on CDP evasion injection: {e}")

    @staticmethod
    def human_type(element, text: str, min_delay: float = 0.04, max_delay: float = 0.12):
        """
        Types text with realistic human typing speed variation and micro-pauses.
        """
        try:
            element.clear()
        except Exception:
            pass

        for char in str(text):
            element.send_keys(char)
            # Occasional micro-pause simulating thinking or shifting keys
            if random.random() < 0.08:
                time.sleep(random.uniform(0.15, 0.35))
            else:
                time.sleep(random.uniform(min_delay, max_delay))

    @staticmethod
    def human_click(driver, element):
        """
        Moves mouse to element with small random offset before clicking.
        """
        try:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(random.uniform(0.4, 0.8))
            
            # Action chains move to simulate mouse movement
            actions = ActionChains(driver)
            actions.move_to_element(element).pause(random.uniform(0.1, 0.3)).click().perform()
        except Exception:
            # Fallback to direct script click if intercepted
            driver.execute_script("arguments[0].click();", element)

    @staticmethod
    def random_sleep(min_s: float = 1.5, max_s: float = 3.5):
        time.sleep(random.uniform(min_s, max_s))
