import math
import random
import time
from typing import List, Tuple
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import selenium_stealth


class InvisibleDotsStealth:
    """
    Stealth & Anti-Bot Evasion Engine inspired by feder-cr/invisible_dots.
    Implements cubic Bézier mouse movement, human keystroke entropy,
    and anti-fingerprinting to evade Cloudflare Turnstile and Datadome.
    """

    @staticmethod
    def create_stealth_driver(headless: bool = False, window_size: Tuple[int, int] = (1440, 900)) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        
        # Core stealth arguments
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        
        if headless:
            options.add_argument("--headless=new")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # Apply selenium-stealth fingerprint spoofing
        selenium_stealth.stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        # Overwrite automation properties via CDP
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.navigator.chrome = { runtime: {}, app: {} };
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """
        })

        return driver

    @staticmethod
    def bezier_curve(p0: Tuple[float, float], p1: Tuple[float, float], 
                     p2: Tuple[float, float], p3: Tuple[float, float], 
                     num_points: int = 25) -> List[Tuple[int, int]]:
        """
        Calculates cubic Bézier coordinates for natural human mouse paths.
        """
        points = []
        for i in range(num_points + 1):
            t = i / float(num_points)
            # Cubic Bezier formula: (1-t)^3*P0 + 3*(1-t)^2*t*P1 + 3*(1-t)*t^2*P2 + t^3*P3
            x = (1 - t)**3 * p0[0] + 3 * (1 - t)**2 * t * p1[0] + 3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0]
            y = (1 - t)**3 * p0[1] + 3 * (1 - t)**2 * t * p1[1] + 3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1]
            points.append((int(round(x)), int(round(y))))
        return points

    @classmethod
    def human_move_and_click(cls, driver: webdriver.Chrome, element) -> bool:
        """
        Simulates realistic human mouse trajectory, hovering, micro-hesitation,
        and click dispatch.
        """
        try:
            # Scroll element smoothly into view
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(random.uniform(0.3, 0.6))

            # Retrieve element bounding box
            rect = driver.execute_script("""
                const r = arguments[0].getBoundingClientRect();
                return {x: r.left + r.width / 2, y: r.top + r.height / 2, width: r.width, height: r.height};
            """, element)

            target_x = rect["x"] + random.uniform(-rect["width"] * 0.2, rect["width"] * 0.2)
            target_y = rect["y"] + random.uniform(-rect["height"] * 0.2, rect["height"] * 0.2)

            # Start point from current or random screen location
            start_x = target_x + random.uniform(-300, 300)
            start_y = target_y + random.uniform(200, 500)

            # Control points for curvature
            ctrl1 = (start_x + random.uniform(-100, 100), (start_y + target_y) / 2 + random.uniform(-50, 50))
            ctrl2 = (target_x + random.uniform(-50, 50), (start_y + target_y) / 2 + random.uniform(-50, 50))

            path = cls.bezier_curve((start_x, start_y), ctrl1, ctrl2, (target_x, target_y), num_points=15)

            # Dispatch mousemove events along trajectory
            for pt in path:
                driver.execute_script("""
                    const evt = new MouseEvent('mousemove', {
                        clientX: arguments[0],
                        clientY: arguments[1],
                        bubbles: true
                    });
                    document.dispatchEvent(evt);
                """, pt[0], pt[1])
                time.sleep(random.uniform(0.005, 0.015))

            # Hover pause
            time.sleep(random.uniform(0.1, 0.25))

            # Dispatch mousedown, mouseup, click
            driver.execute_script("""
                const el = arguments[0];
                el.dispatchEvent(new MouseEvent('mouseenter', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                setTimeout(() => {
                    el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                    el.click();
                }, 50);
            """, element)

            time.sleep(random.uniform(0.2, 0.4))
            return True

        except Exception as e:
            logger.debug(f"Human move/click fallback: {e}")
            try:
                driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                return False

    @classmethod
    def human_type(cls, driver: webdriver.Chrome, element, text: str, clear_first: bool = True) -> bool:
        """
        Types text with human cadence, variable keystroke delays, and dispatches
        proper 'input' and 'change' events for React / Vue reactivity.
        """
        try:
            driver.execute_script("arguments[0].focus();", element)
            time.sleep(random.uniform(0.1, 0.2))

            if clear_first:
                element.send_keys(Keys.CONTROL + "a")
                element.send_keys(Keys.BACKSPACE)
                time.sleep(0.1)

            # Type character-by-character with realistic entropy
            for char in str(text):
                element.send_keys(char)
                if char in " ,.-/":
                    time.sleep(random.uniform(0.10, 0.22))
                else:
                    time.sleep(random.uniform(0.03, 0.09))

            # Trigger React/Vue state flush
            driver.execute_script("""
                arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                arguments[0].dispatchEvent(new Event('blur', {bubbles: true}));
            """, element)

            time.sleep(random.uniform(0.15, 0.3))
            return True

        except Exception as e:
            logger.debug(f"Human typing fallback: {e}")
            try:
                element.send_keys(text)
                return True
            except Exception:
                return False

    @classmethod
    def solve_turnstile_if_present(cls, driver: webdriver.Chrome) -> bool:
        """
        Detects and attempts natural human interaction with Cloudflare Turnstile.
        """
        try:
            turnstile_iframes = driver.find_elements(
                By.XPATH,
                "//iframe[contains(@src, 'turnstile') or contains(@src, 'challenges.cloudflare')]"
            )
            if not turnstile_iframes:
                return False

            logger.info("[InvisibleDots] Cloudflare Turnstile detected. Emulating human interaction...")
            iframe = turnstile_iframes[0]
            cls.human_move_and_click(driver, iframe)
            time.sleep(random.uniform(2.5, 4.0))
            return True
        except Exception as e:
            logger.debug(f"Turnstile note: {e}")
            return False

