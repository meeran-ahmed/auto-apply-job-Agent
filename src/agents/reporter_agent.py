import json
import os
import threading
from datetime import datetime
from pathlib import Path
from loguru import logger


class ReporterAgent:
    """
    Central Ledger & Reporting Agent.
    Aggregates real-time applications across all worker agents,
    deduplicates submissions, and compiles a comprehensive executive report.
    """

    def __init__(self, output_dir: str = "data_folder/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.applied_jobs = []
        self.skipped_jobs = []
        self.failed_jobs = []
        self.start_time = datetime.now()
        self._load_existing_ledger()

    def _load_existing_ledger(self):
        success_file = self.output_dir / "success.json"
        if success_file.exists():
            try:
                with open(success_file, "r", encoding="utf-8") as f:
                    self.applied_jobs = json.load(f)
            except Exception:
                self.applied_jobs = []

    def is_already_applied(self, url: str = "", title: str = "", company: str = "") -> bool:
        with self.lock:
            for j in self.applied_jobs:
                if url and j.get("link") == url:
                    return True
                if company and title and j.get("company", "").strip().lower() == company.strip().lower() and j.get("title", "").strip().lower() == title.strip().lower():
                    return True
            return False

    def record_applied(self, title: str, company: str, platform: str, url: str, notes: str = "Submitted successfully"):
        with self.lock:
            record = {
                "title": title,
                "company": company,
                "platform": platform,
                "link": url,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "Applied",
                "notes": notes
            }
            # Check for duplicate
            if not any(j.get("link") == url or (j.get("company") == company and j.get("title") == title) for j in self.applied_jobs):
                self.applied_jobs.append(record)
                self._save_json()
                logger.info(f"[{platform}] Logged successful application: '{title}' at '{company}'")
            self.generate_report()

    def record_skipped(self, title: str, company: str, reason: str):
        with self.lock:
            self.skipped_jobs.append({
                "title": title,
                "company": company,
                "reason": reason,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    def record_failed(self, title: str, company: str, error: str):
        with self.lock:
            self.failed_jobs.append({
                "title": title,
                "company": company,
                "error": error,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    def _save_json(self):
        success_file = self.output_dir / "success.json"
        with open(success_file, "w", encoding="utf-8") as f:
            json.dump(self.applied_jobs, f, indent=4)

    def generate_report(self) -> Path:
        """
        Compiles the full Markdown executive report.
        """
        report_file = self.output_dir / "APPLICATIONS_REPORT.md"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elapsed = datetime.now() - self.start_time
        elapsed_min = round(elapsed.total_seconds() / 60, 1)

        total_applied = len(self.applied_jobs)
        total_skipped = len(self.skipped_jobs)
        total_failed = len(self.failed_jobs)
        total_processed = total_applied + total_skipped + total_failed

        # Calculate platform breakdown
        platforms = {}
        for j in self.applied_jobs:
            p = j.get("platform", "Other")
            platforms[p] = platforms.get(p, 0) + 1

        md_content = f"""# 🚀 OmniSwarm Automated Job Applications Report
**Candidate**: Meeran Ahmed R.  
**Generated At**: {now_str}  
**Elapsed Time**: {elapsed_min} minutes  
**Total Processed**: {total_processed} | **Successfully Applied**: {total_applied}

---

## 📊 Executive Summary

| Metric | Count | Percentage |
| :--- | :--- | :--- |
| **Total Applied** | **{total_applied}** | **{(total_applied / max(total_processed, 1)) * 100:.1f}%** |
| **Skipped (Blacklisted / Applied Before)** | {total_skipped} | {(total_skipped / max(total_processed, 1)) * 100:.1f}% |
| **Failed (Unresolved Blockers)** | {total_failed} | {(total_failed / max(total_processed, 1)) * 100:.1f}% |

### 🌐 Platform Breakdown
"""
        for p, count in platforms.items():
            md_content += f"- **{p}**: {count} jobs applied\n"

        md_content += """
---

## 📝 Submitted Job Applications

| # | Job Title | Company | Platform | Applied At | Link |
| :- | :--- | :--- | :--- | :--- | :--- |
"""
        for idx, job in enumerate(reversed(self.applied_jobs), start=1):
            title = job.get('job_title') or job.get('title') or 'Engineering Role'
            company = job.get('company') or job.get('job_company') or 'Tech Firm'
            platform = job.get('platform') or ('LinkedIn' if 'linkedin.com' in str(job.get('link', '')) else 'Universal ATS')
            applied_at = job.get('timestamp') or 'Recent'
            link = job.get('link', '')
            link_md = f"[View Job]({link})" if link.startswith("http") else "Submitted"
            md_content += f"| {idx} | **{title}** | {company} | `{platform}` | {applied_at} | {link_md} |\n"

        md_content += """
---

## 🎯 Next Steps & Candidate Advice
1. **Inbox Monitoring**: Check your email (`meeranahmed17@gmail.com`) for confirmation emails and direct interview scheduling links.
2. **Follow-Up Cadence**: If a company has not sent an automated acknowledgment within 48 hours, consider finding the engineering manager on LinkedIn and sending a short, polite note.
3. **Resume & Portfolio Readiness**: Keep [`resume.pdf`](file:///d:/job%20auto/aihawk/data_folder/resume.pdf) and your live portfolio (`https://meeran-portfolio.antideploy.app`) online and updated.
"""

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Updated application report generated at: {report_file}")
        return report_file
