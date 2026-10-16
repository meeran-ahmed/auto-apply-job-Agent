import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from loguru import logger


class ReferralReporter:
    """
    Compiles structured recruiter pitches and referral outreach matrix into
    an executive Markdown document and JSON ledger.
    """

    def __init__(self, output_dir: str = "data_folder/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.md_path = self.output_dir / "REFERRAL_OUTREACH.md"
        self.json_path = self.output_dir / "referral_outreach.json"
        self.ledger = self._load_ledger()

    def _load_ledger(self) -> List[Dict]:
        if self.json_path.exists():
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def record_outreach(self, item: Dict):
        """
        Adds or updates an outreach target with deduplication.
        """
        item["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        company = item.get("company", "").strip().lower()
        title = item.get("job_title", "").strip().lower()
        self.ledger = [
            x for x in self.ledger 
            if not (x.get("company", "").strip().lower() == company and x.get("job_title", "").strip().lower() == title)
        ]
        self.ledger.append(item)
        self._save_ledger()

    def _save_ledger(self):
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(self.ledger, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[ReferralReporter] Failed to save JSON ledger: {e}")

    def generate_report(self) -> str:
        """
        Builds the executive Markdown referral matrix.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_contacts = len(self.ledger)

        lines = [
            "# 🎯 Auto Job: Recruiter & Referral Outreach Matrix",
            f"**Generated**: {timestamp} | **Total Outreaches Ready**: {total_contacts}",
            "**Skills Engine**: `li-dm` & `li-human` (De-slopped, zero robotic buzzwords, < 200 char notes)",
            "",
            "> [!TIP]",
            "> **How to Use This Matrix**: After applying to each job on Greenhouse/Lever/Ashby, find the contact on LinkedIn and paste the **200-char connection note**. Once connected, send the **Recruiter DM** or **Peer Referral Pitch** to double your interview chances!",
            "",
            "---",
            ""
        ]

        if not self.ledger:
            lines.append("No recruiter outreach records generated yet.")
        else:
            for idx, item in enumerate(self.ledger, 1):
                company = item.get("company", "Company")
                role = item.get("job_title", "Role")
                contact = item.get("contact_name", "Hiring Contact")
                contact_role = item.get("contact_role", "Recruiting")
                profile_url = item.get("profile_url", "#")
                note = item.get("connection_note", "")
                recruiter_dm = item.get("recruiter_dm", "")
                referral_dm = item.get("referral_dm", "")

                lines.append(f"### {idx}. {company} — {role}")
                lines.append(f"- **Target Contact**: [{contact}]({profile_url}) ({contact_role})")
                lines.append("")
                lines.append("#### 📝 1. Connection Request Note (< 200 chars)")
                lines.append("```text")
                lines.append(note)
                lines.append("```")
                lines.append("")
                lines.append("#### ✉️ 2. Recruiter Direct Message (To Talent Acquisition)")
                lines.append("```text")
                lines.append(recruiter_dm)
                lines.append("```")
                lines.append("")
                lines.append("#### 🤝 3. Peer Referral Pitch (To Team Engineer)")
                lines.append("```text")
                lines.append(referral_dm)
                lines.append("```")
                lines.append("")
                lines.append("---")
                lines.append("")

        with open(self.md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"[ReferralReporter] Outreach matrix generated at: {self.md_path}")
        return str(self.md_path)
