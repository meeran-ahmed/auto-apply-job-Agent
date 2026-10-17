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

    def __init__(self, target_positions: List[str] = None, blacklist: List[str] = None, max_days: int = 3):
        self.target_positions = target_positions or [
            "Full Stack Developer", "Full Stack Engineer",
            "Frontend Developer", "React Developer",
            "Implementation Engineer", "Solutions Engineer", "Software Engineer"
        ]
        default_blacklist = [
            "senior", "sr.", "sr ", "staff", "principal", "architect", "lead", 
            "manager", "director", "head of", "vp", "onsite", 
            "intern", "internship", "co-op", "trainee", "student"
        ]
        combined = set((blacklist or []) + default_blacklist)
        self.blacklist = [b.lower() for b in combined]
        self.max_days = max_days
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    def _is_recent(self, raw_date) -> bool:
        """
        Filters for jobs posted within the last `max_days` (default 3 days / 72 hours).
        Supports Unix epoch timestamp, ISO 8601 strings, and RFC 2822 RSS formats.
        """
        if not raw_date:
            return True
        import datetime
        from email.utils import parsedate_to_datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        try:
            if isinstance(raw_date, (int, float)):
                dt = datetime.datetime.fromtimestamp(raw_date, tz=datetime.timezone.utc)
            elif isinstance(raw_date, str):
                raw_str = raw_date.strip()
                try:
                    clean_str = raw_str.replace("Z", "+00:00")
                    dt = datetime.datetime.fromisoformat(clean_str)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=datetime.timezone.utc)
                except Exception:
                    dt = parsedate_to_datetime(raw_str)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=datetime.timezone.utc)
            else:
                return True
            diff = now - dt
            return 0 <= diff.total_seconds() <= (self.max_days * 86400)
        except Exception:
            return True

    def fetch_all_jobs(self) -> List[Dict[str, str]]:
        jobs = []
        jobs.extend(self._fetch_greenhouse_boards())
        jobs.extend(self._fetch_jobicy())
        jobs.extend(self._fetch_weworkremotely())
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
                
        logger.info(f"RemotePortalAgent discovered {len(unique_jobs)} fresh (past {self.max_days} days) matching tech jobs across global remote feeds.")
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

    def _fetch_greenhouse_boards(self) -> List[Dict[str, str]]:
        """
        Directly queries Greenhouse job boards for premier tech companies
        for software, full-stack, frontend, and python roles updated in the last 3 days.
        """
        companies = [
            'gitlab', 'stripe', 'figma', 'vercel', 'supabase', 'cloudflare', 'canonical',
            'automattic', 'tailscale', 'docker', 'reddit', 'pinterest', 'discord', 'mozilla',
            'datadog', 'elastic', 'mongodb', 'hashicorp', 'postman', 'grafana', 'cockroachlabs',
            'sourcegraph', 'sentry', 'temporal', 'dbtlabs', 'chainlink', 'remote', 'affirm',
            'benchling', 'gusto', 'instacart', 'lyft', 'okta', 'robinhood', 'samsara'
        ]
        results = []
        for c in companies:
            try:
                resp = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{c}/jobs", headers=self.headers, timeout=4)
                if resp.status_code == 200:
                    for j in resp.json().get("jobs", []):
                        title = j.get("title", "")
                        updated = j.get("updated_at", "")
                        url = j.get("absolute_url", "")
                        if self._matches_target(title) and url and self._is_recent(updated):
                            results.append({
                                "title": title,
                                "company": c.capitalize(),
                                "url": url,
                                "platform": "Greenhouse / Direct Career Board",
                                "location": "Remote",
                                "date_posted": updated
                            })
            except Exception as e:
                logger.debug(f"Greenhouse board fetch note for {c}: {e}")
        return results

    def _fetch_jobicy(self) -> List[Dict[str, str]]:
        results = []
        endpoints = [
            "https://jobicy.com/api/v2/remote-jobs?count=100&industry=engineering",
            "https://jobicy.com/api/v2/remote-jobs?count=100&industry=dev",
            "https://jobicy.com/api/v2/remote-jobs?count=100&industry=tech",
            "https://jobicy.com/api/v2/remote-jobs?count=100&tag=startup",
            "https://jobicy.com/api/v2/remote-jobs?count=100&tag=fullstack"
        ]
        for url in endpoints:
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json().get("jobs", [])
                    for item in data:
                        title = item.get("jobTitle", "")
                        pub_date = item.get("pubDate", "")
                        if self._matches_target(title) and self._is_recent(pub_date):
                            results.append({
                                "title": title,
                                "company": item.get("companyName", "Tech Company"),
                                "url": item.get("url", ""),
                                "platform": "Jobicy / Remote Board",
                                "location": "Remote",
                                "date_posted": pub_date
                            })
            except Exception as e:
                logger.debug(f"Jobicy fetch note: {e}")
        return results

    def _fetch_himalayas(self) -> List[Dict[str, str]]:
        url = "https://himalayas.app/jobs/api?limit=100"
        results = []
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("jobs", [])
                for item in data:
                    title = item.get("title", "")
                    pub_date = item.get("pubDate") or item.get("publishedAt") or item.get("createdAt")
                    apply_link = item.get("applicationLink") or f"https://himalayas.app/jobs/{item.get('guid', '')}"
                    if self._matches_target(title) and apply_link and self._is_recent(pub_date):
                        results.append({
                            "title": title,
                            "company": item.get("companyName", "Tech Company"),
                            "url": apply_link,
                            "platform": "Himalayas / Remote Tech",
                            "location": "Remote",
                            "date_posted": str(pub_date) if pub_date else ""
                        })
        except Exception as e:
            logger.debug(f"Himalayas fetch note: {e}")
        return results

    def _fetch_remotive(self) -> List[Dict[str, str]]:
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=100"
        results = []
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("jobs", [])
                for item in data:
                    title = item.get("title", "")
                    pub_date = item.get("publication_date", "")
                    if self._matches_target(title) and self._is_recent(pub_date):
                        results.append({
                            "title": title,
                            "company": item.get("company_name", "Tech Startup"),
                            "url": item.get("url", ""),
                            "platform": "Remotive / Startup Board",
                            "location": "Remote",
                            "date_posted": pub_date
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
                        pub_date = item.get("date", "")
                        apply_url = item.get("apply_url") or item.get("url") or ""
                        if self._matches_target(title) and apply_url and self._is_recent(pub_date):
                            results.append({
                                "title": title,
                                "company": item.get("company", "Tech Company"),
                                "url": apply_url,
                                "platform": "RemoteOK",
                                "location": "Remote",
                                "date_posted": str(pub_date) if pub_date else ""
                            })
        except Exception as e:
            logger.debug(f"RemoteOK fetch note: {e}")
        return results

    def _fetch_weworkremotely(self) -> List[Dict[str, str]]:
        """
        Scans WeWorkRemotely RSS feeds for live developer roles posted in the last 3 days.
        """
        import xml.etree.ElementTree as ET
        urls = [
            "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
            "https://weworkremotely.com/categories/remote-programming-jobs.rss",
            "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
            "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss"
        ]
        results = []
        for url in urls:
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    for item in root.findall(".//item"):
                        raw_title = item.find("title").text if item.find("title") is not None else ""
                        pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                        link = item.find("link").text if item.find("link") is not None else ""
                        
                        # WWR titles are usually formatted: "Company Name: Job Title"
                        if ":" in raw_title:
                            company, title = raw_title.split(":", 1)
                            company = company.strip()
                            title = title.strip()
                        else:
                            company = "Tech Company"
                            title = raw_title.strip()

                        if self._matches_target(title) and link and self._is_recent(pub_date):
                            results.append({
                                "title": title,
                                "company": company,
                                "url": link,
                                "platform": "WeWorkRemotely",
                                "location": "Remote",
                                "date_posted": pub_date
                            })
            except Exception as e:
                logger.debug(f"WWR fetch note: {e}")
        return results

    def _fetch_arbeitnow(self) -> List[Dict[str, str]]:
        results = []
        for page in range(1, 4):
            url = f"https://www.arbeitnow.com/api/job-board-api?page={page}"
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    for item in data:
                        title = item.get("title", "")
                        pub_date = item.get("created_at")
                        is_remote = item.get("remote", False)
                        if is_remote and self._matches_target(title) and self._is_recent(pub_date):
                            results.append({
                                "title": title,
                                "company": item.get("company_name", "Tech Firm"),
                                "url": item.get("url", ""),
                                "platform": "Arbeitnow / European Tech",
                                "location": "Remote",
                                "date_posted": str(pub_date) if pub_date else ""
                            })
            except Exception as e:
                logger.debug(f"Arbeitnow fetch note: {e}")
        return results
