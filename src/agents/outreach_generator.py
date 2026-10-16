import re
import json
import yaml
from pathlib import Path
from loguru import logger
import google.generativeai as genai


class OutreachGenerator:
    """
    Synthesizes humanized recruiter messages, referral pitches, and 200-char connection notes
    using Google Gemini 1.5 Flash and the `li-dm` / `li-human` skill specifications.
    """

    def __init__(self, secrets_path: str = "data_folder/secrets.yaml", resume_yaml_path: str = "data_folder/plain_text_resume.yaml"):
        self.secrets_path = Path(secrets_path)
        self.resume_yaml_path = Path(resume_yaml_path)
        self.api_key = self._load_api_key()
        self.profile = self._load_profile()

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                logger.warning(f"[OutreachGenerator] Failed to initialize Gemini model: {e}")
                self.model = None
        else:
            self.model = None

    def _load_api_key(self) -> str:
        if self.secrets_path.exists():
            try:
                with open(self.secrets_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                return data.get("llm_api_key", "").strip()
            except Exception:
                return ""
        return ""

    def _load_profile(self) -> dict:
        if self.resume_yaml_path.exists():
            try:
                with open(self.resume_yaml_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                return {}
        return {}

    def _clean_humanize(self, text: str) -> str:
        """
        Applies `li-human` rules: strips em-dashes, deletes buzzwords, ensures authentic tone.
        """
        # 1. Remove em-dashes and en-dashes
        text = text.replace("—", ", ").replace("–", "-")
        
        # 2. Strip AI slop buzzwords
        buzzwords = [
            r"\bthrilled\b", r"\bspearheaded\b", r"\bdelighted\b",
            r"\bpassion(?:ate)?\b", r"\bsynergy\b", r"\btestament\b",
            r"\bgame-changer\b", r"\bdeep dive\b", r"\bleverage\b", r"\bpivotal\b"
        ]
        for b in buzzwords:
            text = re.sub(b, "", text, flags=re.IGNORECASE)
            
        # Clean extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def generate_pitch(self, company: str, job_title: str, contact_name: str = "Hiring Team", contact_role: str = "Recruiter") -> dict:
        """
        Generates connection note, recruiter DM, and referral request.
        """
        pers = self.profile.get("personal_information", {})
        candidate_name = f"{pers.get('name', '')} {pers.get('surname', '')}".strip() or "Meeran Ahmed"
        portfolio = pers.get("portfolio", "") or "https://meeran-portfolio.antideploy.app"
        email = pers.get("email", "")

        # Try LLM generation via Gemini 1.5 Flash
        if self.model:
            prompt = f"""
You are an elite career agent generating recruiter outreach using `li-dm` and `li-human` specifications.

Candidate: {candidate_name}
Portfolio / Links: {portfolio}
Target Company: {company}
Target Role: {job_title}
Contact Person: {contact_name} ({contact_role})

STRICT RULES:
1. `connection_note`: Max 190 characters strictly (LinkedIn limit is 200). Mention the role and candidate's core stack.
2. `recruiter_dm`: Max 90 words. Direct, humble, states application submitted, offers portfolio.
3. `referral_dm`: Max 80 words. Peer-to-peer tone. Asks if they can pass resume internally or review work.
4. NO em-dashes (—). NO AI fluff like "thrilled", "passionate", "spearheaded". Simple, clear English.

Respond ONLY with valid JSON:
{{
  "connection_note": "string under 190 chars",
  "recruiter_dm": "string under 90 words",
  "referral_dm": "string under 80 words"
}}
"""
            try:
                response = self.model.generate_content(prompt)
                raw = response.text.strip()
                # Clean code blocks if present
                if raw.startswith("```json"):
                    raw = raw[7:]
                if raw.startswith("```"):
                    raw = raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                
                res = json.loads(raw.strip())
                return {
                    "connection_note": self._clean_humanize(res.get("connection_note", ""))[:195],
                    "recruiter_dm": self._clean_humanize(res.get("recruiter_dm", "")),
                    "referral_dm": self._clean_humanize(res.get("referral_dm", "")),
                    "company": company,
                    "job_title": job_title,
                    "contact_name": contact_name,
                    "contact_role": contact_role
                }
            except Exception as e:
                logger.debug(f"[OutreachGenerator] Gemini inference note: {e}")

        # Humanized high-converting fallback
        if any(term in contact_name.lower() for term in ["team", "acquisition", "recruiting", "recruiter", "hiring"]):
            greeting = f"Hi {company} team"
        elif contact_name and len(contact_name.split()) > 0 and contact_name.strip() != "Hiring Team":
            greeting = f"Hi {contact_name.split()[0]}"
        else:
            greeting = "Hi there"

        note = f"{greeting}, saw the {job_title} role at {company}. I build with React and Python. Would love to connect!"
        if len(note) > 195:
            note = f"{greeting}, applied for {job_title} at {company}. Would love to connect and share my work."

        recruiter_msg = (
            f"{greeting}, I recently submitted my application for the {job_title} opening at {company}. "
            f"I have hands-on experience building full-stack applications with React, TypeScript, and Python. "
            f"You can view my projects and live demos here: {portfolio}. I would welcome the opportunity to discuss how I can contribute to the team."
        )

        referral_msg = (
            f"{greeting}, hope you're having a good week. I came across the {job_title} role at {company} and love the engineering team's work. "
            f"I build full-stack web systems (portfolio: {portfolio}). If you're open to it, could you pass my profile to the hiring team as an internal referral? "
            f"Happy to answer any questions about my background."
        )

        return {
            "connection_note": self._clean_humanize(note)[:195],
            "recruiter_dm": self._clean_humanize(recruiter_msg),
            "referral_dm": self._clean_humanize(referral_msg),
            "company": company,
            "job_title": job_title,
            "contact_name": contact_name,
            "contact_role": contact_role
        }
