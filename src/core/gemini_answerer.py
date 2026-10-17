import os
import yaml
import json
from pathlib import Path
from loguru import logger
import google.generativeai as genai


class GeminiAnswerer:
    """
    Intelligent Form Questionnaire Answerer using Gemini 1.5 Flash.
    Answers employer screening questions (experience years, notice period,
    salary expectations, tech stack familiarity, custom open text) grounded in candidate profile.
    """

    def __init__(self, secrets_path: str = "data_folder/secrets.yaml", resume_path: str = "data_folder/plain_text_resume.yaml", api_key: str = None):
        self.secrets_path = Path(secrets_path)
        self.resume_path = Path(resume_path)
        self.api_key = api_key or self._load_api_key()
        self.profile = self._load_profile()
        self.model = None

        if self.api_key and not self.api_key.startswith("AQ."):
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("[GeminiAnswerer] Initialized Gemini 1.5 Flash AI Engine.")
            except Exception as e:
                logger.warning(f"[GeminiAnswerer] Failed to initialize Gemini model: {e}")

    def _load_api_key(self) -> str:
        if self.secrets_path.exists():
            try:
                with open(self.secrets_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                return data.get("llm_api_key", "").strip()
            except Exception:
                pass
        return ""

    def _load_profile(self) -> dict:
        if self.resume_path.exists():
            try:
                with open(self.resume_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {}

    def answer_question(self, question: str, options: list = None, job_title: str = "") -> str:
        """
        Determines the most accurate answer for a given field or employer question.
        """
        q_lower = question.lower()

        # 1. High-frequency deterministic answers
        if any(w in q_lower for w in ["notice period", "notice"]):
            return "Immediate (0-15 days)" if not options else self._pick_closest(options, ["immediate", "15 days", "1 month"])
        
        if any(w in q_lower for w in ["authorized", "authorization", "legally eligible", "work permit"]):
            return "Yes" if not options else self._pick_closest(options, ["yes"])

        if any(w in q_lower for w in ["sponsorship", "require visa", "sponsorship in future"]):
            return "No" if not options else self._pick_closest(options, ["no"])

        if any(w in q_lower for w in ["experience", "years of experience", "how many years"]):
            if any(t in q_lower for t in ["python", "react", "full stack", "frontend", "javascript", "web"]):
                return "3" if not options else self._pick_closest(options, ["2-4 years", "3 years", "2", "3"])
            return "2" if not options else self._pick_closest(options, ["1-2 years", "2 years", "1", "2"])

        if any(w in q_lower for w in ["expected salary", "ctc", "compensation"]):
            return "Negotiable as per company standards" if not options else options[0]

        if any(w in q_lower for w in ["portfolio", "website", "personal site", "github"]):
            pers = self.profile.get("personal_information", {})
            return pers.get("portfolio", "https://meeran-portfolio.antideploy.app")

        # 2. Dynamic Gemini generation for open-ended questions
        if self.model:
            prompt = f"""
You are answering an employment form field for a software engineering job.
Candidate Name: Meeran Ahmed R.
Primary Stack: React, TypeScript, Python, FastAPI, Django, PostgreSQL, TailwindCSS.
Portfolio: https://meeran-portfolio.antideploy.app
Target Role: {job_title}
Question: "{question}"
Available Options: {options if options else 'None (free text field)'}

Rules:
1. If options are provided, output EXACTLY ONE of the available option strings.
2. If free text, answer directly, professionally, and concisely in under 40 words.
3. No AI fluff like "I am thrilled" or "spearheaded". Simple authentic tone.
Answer:
"""
            try:
                res = self.model.generate_content(prompt)
                answer = res.text.strip().replace('"', '')
                if options:
                    return self._pick_closest(options, [answer])
                return answer
            except Exception as e:
                logger.debug(f"[GeminiAnswerer] Fallback used: {e}")

        if options:
            return options[0]
        return "Yes, I have hands-on experience in full-stack web and Python development."

    def _pick_closest(self, options: list, targets: list) -> str:
        for t in targets:
            for opt in options:
                if t.lower() in opt.lower():
                    return opt
        return options[0] if options else ""
