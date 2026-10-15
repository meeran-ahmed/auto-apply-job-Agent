import os
import time
import yaml
from pathlib import Path
from loguru import logger
from src.agents.reporter_agent import ReporterAgent
from src.agents.remote_portal_agent import RemotePortalAgent
from src.agents.ats_agent import ATSAgent
from src.utils import chrome_browser_options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


class SwarmOrchestrator:
    """
    OmniSwarm Master Orchestrator.
    Manages concurrent discovery, application dispatching across multiple job platforms,
    and automatic executive reporting.
    """

    def __init__(self, config_path: str = "data_folder/config.yaml", resume_path: str = "data_folder/resume.pdf"):
        self.config_path = config_path
        self.resume_path = os.path.abspath(resume_path) if os.path.exists(resume_path) else None
        self.reporter = ReporterAgent()
        self.profile_data = self._load_profile()
        self.config = self._load_config()

    def _load_profile(self) -> dict:
        try:
            with open("data_folder/plain_text_resume.yaml", "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _load_config(self) -> dict:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def run_swarm(self, max_external_jobs: int = 50):
        logger.info("=" * 60)
        logger.info("[OMNISWARM] STARTING MULTI-AGENT APPLICATION SWARM")
        logger.info("=" * 60)

        # 1. Agent: Remote Tech Discovery
        logger.info("[Agent: Discovery] Scanning global remote tech job feeds...")
        discovery_agent = RemotePortalAgent(self.config.get("positions", []))
        discovered_jobs = discovery_agent.fetch_all_jobs()
        logger.info(f"[Agent: Discovery] Found {len(discovered_jobs)} matching engineering positions.")

        # 2. Agent: Parallel ATS Worker
        if discovered_jobs:
            logger.info("[Agent: ATS Worker] Initializing dedicated ATS browser worker...")
            try:
                options = chrome_browser_options()
                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                ats_worker = ATSAgent(
                    driver=driver,
                    resume_path=self.resume_path,
                    profile_data=self.profile_data,
                    gpt_answerer=None,
                    reporter=self.reporter
                )

                # Process jobs up to limit
                processed_count = 0
                for job in discovered_jobs:
                    if processed_count >= max_external_jobs:
                        break
                    
                    if self.reporter.is_already_applied(job.get("url"), job.get("title"), job.get("company")):
                        logger.info(f"[Swarm Orchestrator] Skipping already applied job: {job.get('title')} at {job.get('company')}")
                        continue

                    logger.info(f"[Swarm Orchestrator] Dispatching job {processed_count + 1}/{max_external_jobs}: {job.get('title')} at {job.get('company')}")
                    ats_worker.process_job(job)
                    processed_count += 1
                    time.sleep(2)

                try:
                    driver.quit()
                except Exception:
                    pass

            except Exception as e:
                logger.error(f"[Swarm Orchestrator] ATS worker error: {e}")

        # 3. Agent: Reporter compiles final document
        report_path = self.reporter.generate_report()
        logger.info("=" * 60)
        logger.info(f"[SUCCESS] SWARM RUN COMPLETE! Final report saved to: {report_path}")
        logger.info("=" * 60)
        return report_path

    def run_excel_batch(self, file_path: str = None, max_jobs: int = 100):
        from src.agents.excel_batch_agent import ExcelBatchAgent
        logger.info("=" * 60)
        logger.info("[OMNISWARM] STARTING SPREADSHEET (EXCEL/CSV) BATCH AUTO-APPLY")
        logger.info("=" * 60)

        excel_agent = ExcelBatchAgent(file_path)
        jobs = excel_agent.parse_jobs()
        if not jobs:
            logger.warning("[Swarm Orchestrator] No jobs found in spreadsheet to process.")
            return self.reporter.generate_report()

        logger.info(f"[Swarm Orchestrator] Loaded {len(jobs)} jobs from spreadsheet. Initializing ATS worker...")
        try:
            options = chrome_browser_options()
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            ats_worker = ATSAgent(
                driver=driver,
                resume_path=self.resume_path,
                profile_data=self.profile_data,
                gpt_answerer=None,
                reporter=self.reporter
            )

            processed_count = 0
            for job in jobs:
                if processed_count >= max_jobs:
                    break

                if self.reporter.is_already_applied(job.get("url"), job.get("title"), job.get("company")):
                    logger.info(f"[Swarm Orchestrator] Skipping already applied job: {job.get('title')} at {job.get('company')}")
                    continue

                logger.info(f"[Swarm Orchestrator] Processing spreadsheet job {processed_count + 1}/{min(len(jobs), max_jobs)}: '{job.get('title')}' at '{job.get('company')}' -> {job.get('url')}")
                ats_worker.process_job(job)
                processed_count += 1
                time.sleep(2)

            try:
                driver.quit()
            except Exception:
                pass

        except Exception as e:
            logger.error(f"[Swarm Orchestrator] Error during spreadsheet batch run: {e}")

        report_path = self.reporter.generate_report()
        logger.info("=" * 60)
        logger.info(f"[SUCCESS] SPREADSHEET BATCH RUN COMPLETE! Final report saved to: {report_path}")
        logger.info("=" * 60)
        return report_path

