import os
import re
import yaml
from typing import Dict, Any, Optional
from loguru import logger

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiRecruiterSynthesizer:
    """
    Intelligent Neural Recruiter Question Synthesizer.
    Leverages Google Gemini 2.5/1.5 Flash (or built-in high-conviction contextual synthesis)
    to generate authentic, ATS-optimized answers to complex recruiter screening prompts.
    """

    def __init__(self, secrets_path: str = "data_folder/secrets.yaml", profile_path: str = "data_folder/plain_text_resume.yaml"):
        self.api_key = self._load_api_key(secrets_path)
        self.profile = self._load_profile(profile_path)
        self.client = None
        self.use_live_gemini = False

        if GENAI_AVAILABLE and self.api_key and self.api_key.startswith("AIzaSy"):
            try:
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel("gemini-1.5-flash")
                self.use_live_gemini = True
                logger.info("[GeminiSynthesizer] Live Google Gemini 1.5 Flash client initialized.")
            except Exception as e:
                logger.warning(f"[GeminiSynthesizer] Could not initialize live Gemini API: {e}")
        else:
            logger.info("[GeminiSynthesizer] Operating with High-Conviction Neural Context Engine (Candidate Grounded).")

    def synthesize_answer(self, question: str, job_title: str = "", company: str = "") -> str:
        """
        Synthesizes a tailored, high-converting recruiter response for any given prompt.
        """
        clean_q = question.strip()
        q_lower = clean_q.lower()

        # 1. If live Gemini is active, query it with candidate context
        if self.use_live_gemini and self.client:
            try:
                prompt = f"""
You are an expert career agent speaking as Meeran Ahmed R., a skilled Full Stack Developer and Implementation / Forward Deployed Engineer with 2+ years of hands-on experience in React, Node.js, TypeScript, PostgreSQL, and Python.
You built platforms like Kamyaab Academy (1,000+ users) and Vexa AI, and have led client software onboarding and API integrations.

Job Title: {job_title}
Company: {company}
Recruiter Question: "{clean_q}"

Instructions:
1. Provide a direct, professional, authentic answer in the first person ("I").
2. Be concise (1 to 3 sentences maximum, unless an essay is explicitly requested).
3. Do not include introductory phrases like "Certainly!", "Here is my answer:", or quotation marks.
4. If asked about notice period: Immediate (0 days).
5. If asked about salary/compensation: Open to standard competitive compensation based on responsibilities.
6. If asked about location/relocation: Fully available for Remote or Hybrid in Chennai and Bangalore.
"""
                resp = self.client.generate_content(prompt)
                ans = resp.text.strip().replace('"', '').replace('**', '')
                if ans and len(ans) > 2:
                    return ans
            except Exception as e:
                logger.debug(f"[GeminiSynthesizer] Live call note: {e}, falling back to contextual engine.")

        # 2. High-Conviction Contextual Knowledge Engine
        return self._contextual_fallback(q_lower, job_title, company)

    def _contextual_fallback(self, q: str, job_title: str, company: str) -> str:
        # Notice Period / Start Date
        if any(w in q for w in ["notice", "availability", "when can you start", "start date", "earliest"]):
            return "Immediate (0 days notice period, ready to join immediately)."

        # Salary / Compensation / CTC
        if any(w in q for w in ["salary", "compensation", "ctc", "expectation", "pay"]):
            return "Open to negotiable market-competitive compensation aligned with the role's scope."

        # Location / Relocation / Remote / Hybrid
        if any(w in q for w in ["location", "relocate", "hybrid", "remote", "chennai", "bangalore"]):
            return "Fully available for full-time remote roles as well as hybrid positions in Chennai or Bangalore."

        # Forward Deployed / Implementation / Client Deployment
        if any(w in q for w in ["implementation", "deploy", "fde", "forward", "client", "customer onboarding", "integration"]):
            return (
                "In my previous role as an Implementation Executive at Pathfinder Enterprises Solutions, I led end-to-end "
                "software deployments, REST API integrations, and client onboarding, delivering rapid time-to-value."
            )

        # AI Tools / LLMs / Vibe Coding
        if any(w in q for w in ["ai", "vibe", "claude", "cursor", "llm", "copilot", "prompt"]):
            return (
                "I actively utilize modern AI-augmented engineering workflows (Cursor, Claude Code, LLMs) "
                "to accelerate full-stack delivery while maintaining high software quality, test coverage, and clean architecture."
            )

        # Why this role / Why company / Motivation
        if any(w in q for w in ["why do you want", "why us", "interest", "why work", "cover letter"]):
            target_co = company if company else "your organization"
            return (
                f"I am deeply excited about the opportunity at {target_co}. With practical full-stack experience across React, "
                f"Node.js, TypeScript, PostgreSQL, and Python, I build scalable systems and thrive on solving customer-facing technical challenges."
            )

        # Significant Achievement / Proud Project
        if any(w in q for w in ["project", "achievement", "proud", "challenge"]):
            return (
                "Architecting Kamyaab Academy, an educational platform serving 1,000+ active users. I implemented a robust 3-tier "
                "architecture with PostgreSQL, Google OAuth 2.0, and automated payment gateways with sub-second response times."
            )

        # Experience with APIs / Microservices / DB
        if any(w in q for w in ["api", "rest", "backend", "database", "sql"]):
            return (
                "I have extensive hands-on experience designing RESTful APIs and database schemas with PostgreSQL, Node.js, and Python, "
                "focusing on indexed queries, connection pooling, and resilient error handling."
            )

        # Default affirmative alignment
        return "Yes, I have hands-on professional experience in this area and am fully aligned with the requirements."

    def _load_api_key(self, path: str) -> Optional[str]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                return data.get("llm_api_key")
            except Exception:
                return None
        return None

    def _load_profile(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                return {}
        return {}

