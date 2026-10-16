import requests
import json
from loguru import logger
from typing import List, Dict


class RemotePortalAgent:
    """
    Rapid Discovery Agent for global Remote & Hybrid tech positions.
    Collects live remote jobs matching candidate positions and extracts
    their direct ATS application endpoints (Greenhouse, Lever, Ashby, etc.).
    """

    def __init__(self, target_positions: List[str] = None, blacklist: List[str] = None):
        self.target_positions = target_positions or [
            "Full Stack Developer", "Full Stack Engineer",
            "Frontend Developer", "React Developer",
            "Implementation Engineer", "Solutions Engineer", "Software Engineer"
        ]
        default_blacklist = ["senior", "sr.", "sr ", "staff", "principal", "architect", "lead", "manager", "director", "head of", "vp", "onsite"]
        combined = set((blacklist or []) + default_blacklist)
        self.blacklist = [b.lower() for b in combined]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    def fetch_all_jobs(self) -> List[Dict[str, str]]:
        jobs = []
        jobs.extend(self._fetch_jobicy())
        jobs.extend(self._fetch_himalayas())
        jobs.extend(self._fetch_remotive())
        jobs.extend(self._fetch_remoteok())
        jobs.extend(self._fetch_arbeitnow())
        
        # Deduplicate jobs by URL and title
        unique_jobs = []
        seen_keys = set()
        for j in jobs:
            url = j.get("url", "").strip()
            title = j.get("title", "").strip().lower()
            company = j.get("company", "").strip().lower()
            key = url if url else f"{company}:{title}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_jobs.append(j)
                
        logger.info(f"RemotePortalAgent discovered {len(unique_jobs)} unique matching tech jobs across global remote feeds.")
        return unique_jobs

    def _matches_target(self, title: str) -> bool:
        t = title.lower()
        if any(b in t for b in self.blacklist):
            return False
        keywords = [
            "full stack", "fullstack", "frontend", "front-end", "react",
            "software engineer", "developer", "implementation", "solutions",
            "web", "node", "javascript", "typescript", "python"
        ]
        return any(k in t for k in keywords)

    def _fetch_jobicy(self) -> List[Dict[str, str]]:
        results = []
        endpoints = [
            "https://jobicy.com/api/v2/remote-jobs?count=100&industry=engineering",
            "https://jobicy.com/api/v2/remote-jobs?count=100&industry=dev"
        ]
        for url in endpoints:
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json().get("jobs", [])
                    for item in data:
                        title = item.get("jobTitle", "")
                        if self._matches_target(title):
                            results.append({
                                "title": title,
                                "company": item.get("companyName", "Tech Company"),
                                "url": item.get("url", ""),
                                "platform": "Jobicy / Remote Board",
                                "location": "Remote"
                            })
            except Exception as e:
                logger.debug(f"Jobicy fetch note: {e}")
        return results

    def _fetch_himalayas(self) -> List[Dict[str, str]]:
        url = "https://himalayas.app/jobs/api?limit=50"
        results = []
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("jobs", [])
                for item in data:
                    title = item.get("title", "")
                    apply_link = item.get("applicationLink") or f"https://himalayas.app/jobs/{item.get('guid', '')}"
                    if self._matches_target(title) and apply_link:
                        results.append({
                            "title": title,
                            "company": item.get("companyName", "Tech Company"),
                            "url": apply_link,
                            "platform": "Himalayas / Remote Tech",
                            "location": "Remote"
                        })
        except Exception as e:
            logger.debug(f"Himalayas fetch note: {e}")
        return results

    def _fetch_remotive(self) -> List[Dict[str, str]]:
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=50"
        results = []
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("jobs", [])
                for item in data:
                    title = item.get("title", "")
                    if self._matches_target(title):
                        results.append({
                            "title": title,
                            "company": item.get("company_name", "Tech Startup"),
                            "url": item.get("url", ""),
                            "platform": "Remotive / Startup Board",
                            "location": "Remote"
                        })
        except Exception as e:
            logger.debug(f"Remotive fetch note: {e}")
        return results

    def _fetch_remoteok(self) -> List[Dict[str, str]]:
        url = "https://remoteok.com/api"
        results = []
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for item in data:
                    if isinstance(item, dict):
                        title = item.get("position", "")
                        apply_url = item.get("apply_url") or item.get("url") or ""
                        if self._matches_target(title) and apply_url:
                            results.append({
                                "title": title,
                                "company": item.get("company", "Tech Company"),
                                "url": apply_url,
                                "platform": "RemoteOK",
                                "location": "Remote"
                            })
        except Exception as e:
            logger.debug(f"RemoteOK fetch note: {e}")
        return results

    def _fetch_arbeitnow(self) -> List[Dict[str, str]]:
        url = "https://www.arbeitnow.com/api/job-board-api"
        results = []
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                for item in data:
                    title = item.get("title", "")
                    is_remote = item.get("remote", False)
                    if is_remote and self._matches_target(title):
                        results.append({
                            "title": title,
                            "company": item.get("company_name", "Tech Firm"),
                            "url": item.get("url", ""),
                            "platform": "Arbeitnow / European Tech",
                            "location": "Remote"
                        })
        except Exception as e:
            logger.debug(f"Arbeitnow fetch note: {e}")
        return results
