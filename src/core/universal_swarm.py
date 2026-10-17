import os
import yaml
from pathlib import Path
from loguru import logger
from src.core.chrome_bridge import ChromeBridge
from src.core.gemini_answerer import GeminiAnswerer
from src.agents.reporter_agent import ReporterAgent
from src.portals.naukri_agent import NaukriAgent
from src.portals.indeed_agent import IndeedAgent
from src.portals.cutshort_agent import CutshortAgent
from src.portals.internshala_jobs_agent import InternshalaJobsAgent
from src.portals.wellfound_agent import WellfoundAgent


class UniversalSwarm:
    """
    Universal Swarm Orchestrator.
    Connects directly to the user's live Chrome browser session (meeranahmed17@gmail.com)
    on port 9222 and dispatches specialized worker agents across all major portals
    with zero login walls, intelligent Gemini question-answering, and verified submissions.
    """

    AVAILABLE_PORTALS = ["naukri", "indeed", "cutshort", "internshala", "wellfound"]

    def __init__(self, port: int = 9222, gemini_api_key: str = None):
        self.port = port
        self.bridge = ChromeBridge(port=port)
        self.reporter = ReporterAgent()
        self.gemini_key = gemini_api_key or self._resolve_gemini_key()
        self.answerer = GeminiAnswerer(api_key=self.gemini_key)
        self.driver = None

    def _resolve_gemini_key(self) -> str:
        key = os.environ.get("GEMINI_API_KEY")
        if key:
            return key
        try:
            secrets_path = Path("data_folder/secrets.yaml")
            if secrets_path.exists():
                with open(secrets_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    return data.get("gemini_api_key", "")
        except Exception:
            pass
        return ""

    def connect(self):
        """Attaches to the active Chrome debugging session."""
        if not self.driver:
            logger.info(f"[UniversalSwarm] Connecting to live Chrome on port {self.port}...")
            self.driver = self.bridge.launch_or_attach()
        return self.driver

    def run_portal(self, portal_name: str, keyword: str = "Full Stack Developer", limit: int = 10) -> int:
        """Runs a single portal worker agent."""
        portal_name = portal_name.lower().strip()
        driver = self.connect()

        logger.info(f"[UniversalSwarm] Dispatching agent for portal: '{portal_name.upper()}' (Target: {limit} jobs)")

        if portal_name == "naukri":
            agent = NaukriAgent(driver=driver, gemini_answerer=self.answerer, reporter=self.reporter)
            return agent.search_and_apply(keyword=keyword, max_jobs=limit)

        elif portal_name == "indeed":
            agent = IndeedAgent(driver=driver, gemini_answerer=self.answerer, reporter=self.reporter)
            return agent.search_and_apply(keyword=keyword, max_jobs=limit)

        elif portal_name == "cutshort":
            agent = CutshortAgent(driver=driver, gemini_answerer=self.answerer, reporter=self.reporter)
            return agent.search_and_apply(keyword=keyword, max_jobs=limit)

        elif portal_name in ["internshala", "internshala_jobs"]:
            agent = InternshalaJobsAgent(driver=driver, gemini_answerer=self.answerer, reporter=self.reporter)
            return agent.search_and_apply(keyword="web-development", max_jobs=limit)

        elif portal_name in ["wellfound", "angellist"]:
            agent = WellfoundAgent(driver=driver, gemini_answerer=self.answerer, reporter=self.reporter)
            return agent.search_and_apply(keyword=keyword, max_jobs=limit)

        else:
            logger.error(f"[UniversalSwarm] Unknown or unconfigured portal: '{portal_name}'. Available: {self.AVAILABLE_PORTALS}")
            return 0

    def run_swarm(self, portals=None, limit_per_portal: int = 5, keyword: str = "Full Stack Developer") -> str:
        """
        Executes multi-portal swarm across selected or all platforms sequentially.
        """
        target_portals = portals or self.AVAILABLE_PORTALS
        logger.info("=" * 60)
        logger.info(f"[UNIVERSAL SWARM] Commencing across portals: {', '.join(target_portals).upper()}")
        logger.info("=" * 60)

        total_applied = 0
        for p in target_portals:
            try:
                count = self.run_portal(portal_name=p, keyword=keyword, limit=limit_per_portal)
                total_applied += count
                logger.info(f"[UniversalSwarm] Completed {p.upper()}: {count} verified submissions.")
            except Exception as e:
                logger.error(f"[UniversalSwarm] Error while running agent for {p}: {e}")

        final_report = self.reporter.generate_report()
        logger.info(f"[UniversalSwarm] Swarm run complete! Total verified applied: {total_applied}")
        logger.info(f"[UniversalSwarm] Executive Report: {final_report}")
        return final_report
