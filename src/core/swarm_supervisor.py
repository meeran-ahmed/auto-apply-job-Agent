import os
import sys
import time
import json
import queue
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

from src.core.stealth_engine import InvisibleDotsStealth
from src.ats.universal_applier import UniversalATSApplier
from src.llm.gemini_synthesizer import GeminiRecruiterSynthesizer
from src.agents.reporter_agent import ReporterAgent


class SwarmSupervisor:
    """
    Multi-Agent Swarm Orchestrator inspired by Anil-matcha/open-duet.
    Coordinates concurrent stealth workers, handles thread-safe job distribution,
    and guarantees zero-false-positive terminal verification.
    """

    def __init__(self, resume_path: str = "data_folder/resume.pdf", 
                 profile_path: str = "data_folder/plain_text_resume.yaml",
                 max_concurrency: int = 2,
                 headless: bool = False):
        self.resume_path = os.path.abspath(resume_path)
        self.profile_path = os.path.abspath(profile_path)
        self.max_concurrency = max_concurrency
        self.headless = headless
        
        self.job_queue: queue.Queue = queue.Queue()
        self.reporter = ReporterAgent()
        self.synthesizer = GeminiRecruiterSynthesizer()
        
        import yaml
        with open(self.profile_path, "r", encoding="utf-8") as f:
            self.profile_data = yaml.safe_load(f) or {}

        self.applied_count = 0
        self.failed_count = 0
        self.lock = threading.Lock()
        self.active_workers: List[threading.Thread] = []

    def load_jobs(self, jobs: List[Dict[str, Any]], target_limit: int = 50):
        """Loads and deduplicates target jobs into the synchronized swarm queue."""
        queued = 0
        for job in jobs:
            if queued >= target_limit:
                break
            url = job.get("url", "")
            title = job.get("title", "")
            company = job.get("company", "")
            
            if not url or self.reporter.is_already_applied(url, title, company):
                continue
            
            self.job_queue.put(job)
            queued += 1

        logger.info(f"[SwarmSupervisor] Successfully queued {queued} prioritized positions for multi-agent dispatch.")

    def run_swarm(self):
        """Launches the concurrent worker swarm."""
        logger.info(f"[SwarmSupervisor] Launching swarm with {self.max_concurrency} concurrent stealth workers...")
        start_time = time.time()

        for worker_id in range(1, self.max_concurrency + 1):
            t = threading.Thread(target=self._worker_loop, args=(worker_id,), daemon=True)
            self.active_workers.append(t)
            t.start()
            time.sleep(1.5)  # Staggered startup to avoid CPU/Display spikes

        # Wait for all jobs in queue to be processed
        self.job_queue.join()

        elapsed = round((time.time() - start_time) / 60, 2)
        logger.info(f"[SwarmSupervisor] Swarm execution complete! Processed in {elapsed} minutes.")
        logger.info(f"Total Confirmed Submissions: {self.applied_count} | Unconfirmed: {self.failed_count}")
        
        report_path = self.reporter.generate_report()
        logger.info(f"Updated Executive Report: {report_path}")

    def _worker_loop(self, worker_id: int):
        """Worker thread lifecycle: creates isolated stealth driver and consumes queue."""
        logger.info(f"[Worker #{worker_id}] Initializing stealth browser environment...")
        driver = None
        try:
            driver = InvisibleDotsStealth.create_stealth_driver(headless=self.headless)
            applier = UniversalATSApplier(
                driver=driver,
                resume_path=self.resume_path,
                profile_data=self.profile_data,
                synthesizer=self.synthesizer
            )
            logger.info(f"[Worker #{worker_id}] Ready for task assignment.")

            while True:
                try:
                    job = self.job_queue.get_nowait()
                except queue.Empty:
                    break

                title = job.get("title", "")
                company = job.get("company", "")
                url = job.get("url", "")
                source = job.get("ats") or job.get("platform") or "ATS Portal"

                logger.info(f"[Worker #{worker_id}] Applying to '{title}' at '{company}'...")
                
                try:
                    applied = applier.apply(title, company, url)
                    with self.lock:
                        if applied:
                            self.applied_count += 1
                            logger.info(f"[Worker #{worker_id}] >>> SUCCESS ({self.applied_count}) Confirmed '{title}' at '{company}'!")
                            self.reporter.record_applied(
                                title=title,
                                company=company,
                                platform=source,
                                url=url,
                                notes=f"OmniSwarm verified submission. Confirmation state validated."
                            )
                            self._append_to_success_json(company, title, url)
                        else:
                            self.failed_count += 1
                            logger.warning(f"[Worker #{worker_id}] --- Form unconfirmed for '{title}' at '{company}'")
                            self.reporter.record_failed(title, company, f"Terminal confirmation not reached on {source}")
                except Exception as ex:
                    logger.error(f"[Worker #{worker_id}] Error processing '{company}': {ex}")
                    with self.lock:
                        self.failed_count += 1
                finally:
                    self.job_queue.task_done()
                    time.sleep(2.0)

        except Exception as e:
            logger.error(f"[Worker #{worker_id}] Fatal initialization error: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.info(f"[Worker #{worker_id}] Browser session closed safely.")
                except Exception:
                    pass

    def _append_to_success_json(self, company: str, title: str, url: str):
        """Maintains clean persistent record in success.json."""
        try:
            success_file = Path("data_folder/output/success.json")
            if success_file.exists():
                with open(success_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = []

            exists = any(item.get("link") == url for item in data)
            if not exists:
                data.append({
                    "company": company,
                    "job_title": title,
                    "link": url,
                    "job_recruiter": f"{company} Talent Acquisition",
                    "job_location": "Remote / Hybrid (India)",
                    "pdf_path": f"file:///{self.resume_path.replace(os.sep, '/')}"
                })
                with open(success_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
        except Exception as e:
            logger.debug(f"Ledger append note: {e}")

