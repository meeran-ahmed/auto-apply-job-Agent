import os
import sys
import time
import subprocess
import requests
from pathlib import Path
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


class ChromeBridge:
    """
    Connects to the user's live Chrome browser (meeranahmed17@gmail.com)
    via Chrome DevTools Protocol (CDP) on port 9222.
    Ensures zero login walls and maintains authenticated sessions across all portals.
    """

    def __init__(self, port: int = 9222):
        self.port = port
        self.debug_url = f"http://127.0.0.1:{self.port}"
        self.user_data_dir = Path(os.environ.get("LOCALAPPDATA", "C:\\Users\\AI EDITION\\AppData\\Local")) / "Google" / "Chrome" / "JobAgentData"

    def is_chrome_debugging_ready(self) -> bool:
        """
        Checks if Chrome is already accepting CDP connections on port 9222.
        """
        try:
            resp = requests.get(f"{self.debug_url}/json/version", timeout=1.5)
            if resp.status_code == 200:
                logger.info(f"[ChromeBridge] Live Chrome instance detected on port {self.port}!")
                return True
        except Exception:
            pass
        return False

    def launch_or_attach(self) -> webdriver.Chrome:
        """
        Launches Chrome with remote debugging if not already running,
        then attaches Selenium directly to the live session.
        """
        if not self.is_chrome_debugging_ready():
            logger.info(f"[ChromeBridge] Starting Chrome with debugging port {self.port}...")
            chrome_exec = self._find_chrome_executable()
            if not chrome_exec or not chrome_exec.exists():
                raise RuntimeError("Google Chrome executable not found on system!")

            self.user_data_dir.mkdir(parents=True, exist_ok=True)
            cmd = [
                str(chrome_exec),
                f"--remote-debugging-port={self.port}",
                f"--user-data-dir={str(self.user_data_dir)}",
                "--no-first-run",
                "--no-default-browser-check"
            ]
            subprocess.Popen(cmd)
            
            # Wait up to 8 seconds for CDP to become ready
            for _ in range(8):
                if self.is_chrome_debugging_ready():
                    break
                time.sleep(1)

        # Attempt CDP connection if port is ready
        if self.is_chrome_debugging_ready():
            try:
                options = webdriver.ChromeOptions()
                options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.port}")
                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                logger.info(f"[ChromeBridge] Successfully attached to live Chrome session! Current URL: {driver.current_url}")
                return driver
            except Exception as e:
                logger.warning(f"[ChromeBridge] CDP attachment failed ({e}). Falling back to standalone stealth driver...")

        # Fallback: Launch dedicated standalone stealth Chrome driver
        logger.info("[ChromeBridge] Initializing dedicated standalone Chrome driver with stealth profile...")
        from src.utils import chrome_browser_options
        options = chrome_browser_options(custom_profile_name="job_agent_stealth_profile")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def _find_chrome_executable(self) -> Path:
        candidates = [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("LOCALAPPDATA", "C:\\Users\\AI EDITION\\AppData\\Local")) / "Google" / "Chrome" / "Application" / "chrome.exe"
        ]
        for p in candidates:
            if p.exists():
                return p
        return Path("chrome.exe")
