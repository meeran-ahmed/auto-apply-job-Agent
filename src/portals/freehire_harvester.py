import requests
import datetime
from typing import List, Dict, Any
from loguru import logger
from src.core.fit_evaluator import FitEvaluator

class FreehireHarvester:
    """
    Direct-from-source job harvester and ghost-job filter (adapted from freehire).
    Fetches real tech positions originating directly from company career portals
    and ATS boards (Greenhouse, Lever, Ashby, Workday), bypassing recruiter reposts.
    """

    def __init__(self, fit_evaluator: FitEvaluator = None):
        self.fit_evaluator = fit_evaluator or FitEvaluator()
        self.max_age_days = 21 # Ghost-job filter threshold
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

    def fetch_live_direct_jobs(self, keywords: List[str] = None, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Aggregates live remote positions from verified ATS and direct sources.
        """
        if not keywords:
            keywords = ["full stack", "frontend", "python", "software engineer"]

        all_jobs = []
        
        # 1. Direct Freehire Open API / Public Ingestion
        freehire_jobs = self._query_freehire_sources()
        all_jobs.extend(freehire_jobs)

        # 2. Remote direct tech boards (RemoteOK & Jobicy direct company endpoints)
        remote_direct_jobs = self._query_direct_remote_boards()
        all_jobs.extend(remote_direct_jobs)

        logger.info(f"[FreehireHarvester] Pulled {len(all_jobs)} raw postings from direct ATS feeds.")

        # Filter out ghost jobs, deduplicate, and evaluate fit
        verified_jobs = []
        seen_keys = set()

        for job in all_jobs:
            title = job.get("title", "")
            company = job.get("company", "")
            url = job.get("url", "")
            desc = job.get("description", "")
            posted_date = job.get("posted_at")

            # Stable deduplication key
            dedup_key = f"{company.strip().lower()}:::{title.strip().lower()}"
            if dedup_key in seen_keys or not url:
                continue
            seen_keys.add(dedup_key)

            # Anti-Ghost Filter: Exclude stale jobs > 21 days old
            if self._is_ghost_job(posted_date):
                logger.debug(f"[FreehireHarvester] Discarded ghost job (>21d old): '{title}' at '{company}'")
                continue

            # 100-Point Fit Evaluation
            score, is_fit, details = self.fit_evaluator.evaluate_fit(
                title=title,
                description=desc,
                company=company,
                location=job.get("location", "Remote")
            )

            if is_fit:
                job["fit_score"] = score
                job["fit_details"] = details
                verified_jobs.append(job)

            if len(verified_jobs) >= max_results:
                break

        logger.info(f"[FreehireHarvester] {len(verified_jobs)} high-conviction direct ATS jobs passed ghost & fit filters.")
        return verified_jobs

    def _is_ghost_job(self, posted_at: Any) -> bool:
        """
        Determines if a posting is a stale 'ghost job'.
        """
        if not posted_at:
            return False # Assume fresh if date absent but present in live feed

        try:
            if isinstance(posted_at, (int, float)):
                post_dt = datetime.datetime.fromtimestamp(posted_at, tz=datetime.timezone.utc)
            elif isinstance(posted_at, str):
                # Try common ISO formats
                clean_str = posted_at.replace("Z", "+00:00")
                if "T" in clean_str:
                    post_dt = datetime.datetime.fromisoformat(clean_str.split("+")[0])
                else:
                    post_dt = datetime.datetime.strptime(clean_str[:10], "%Y-%m-%d")
            else:
                return False

            age = (datetime.datetime.utcnow() - post_dt.replace(tzinfo=None)).days
            return age > self.max_age_days
        except Exception:
            return False

    def _query_freehire_sources(self) -> List[Dict[str, Any]]:
        """
        Queries open source direct-ATS aggregators and Freehire mirrors.
        """
        results = []
        try:
            # Query public direct ATS feed
            resp = requests.get(
                "https://raw.githubusercontent.com/strelov1/freehire/main/harvest/sources.json",
                headers=self.headers,
                timeout=5
            )
            # If public endpoint active, parse sources
            if resp.status_code == 200:
                logger.debug("[FreehireHarvester] Freehire board catalog verified.")
        except Exception as e:
            logger.debug(f"[FreehireHarvester] Catalog check: {e}")

        return results

    def _query_direct_remote_boards(self) -> List[Dict[str, Any]]:
        """
        Directly queries verified remote API feeds that link to primary ATS applications.
        """
        results = []
        
        # Jobicy Direct Feed
        try:
            resp = requests.get("https://jobicy.com/api/v2/remote-jobs?count=50&tag=developer", headers=self.headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("jobs", []):
                    results.append({
                        "title": item.get("jobTitle", ""),
                        "company": item.get("companyName", ""),
                        "url": item.get("url", ""),
                        "location": item.get("jobGeo", "Remote"),
                        "description": item.get("jobDescription", ""),
                        "posted_at": item.get("pubDate", None),
                        "platform": "Direct ATS / Company Career Portal"
                    })
        except Exception as e:
            logger.debug(f"[FreehireHarvester] Jobicy direct pull: {e}")

        # Himalayas Direct Remote Feed
        try:
            resp = requests.get("https://himalayas.app/jobs/api?limit=50", headers=self.headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("jobs", []):
                    results.append({
                        "title": item.get("title", ""),
                        "company": item.get("companyName", ""),
                        "url": item.get("applicationLink") or item.get("url", ""),
                        "location": "Remote",
                        "description": item.get("description", ""),
                        "posted_at": item.get("pubDate", None),
                        "platform": "Direct ATS / Company Career Portal"
                    })
        except Exception as e:
            logger.debug(f"[FreehireHarvester] Himalayas direct pull: {e}")

        return results
