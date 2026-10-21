import os
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple
from loguru import logger
from src.agents.drafter_reviewer import DrafterReviewerEngine

class ResumeTailor:
    """
    Per-Job Dynamic Resume & Cover Letter Customization Engine (adapted from ai-job-search).
    Aligns candidate experience, keywords, and portfolio highlights with the specific
    requirements of each vacancy to maximize ATS scoring and interview callbacks.
    """

    def __init__(self, resume_path: str = "data_folder/plain_text_resume.yaml"):
        self.resume_path = Path(resume_path)
        self.drafter_reviewer = DrafterReviewerEngine()
        self.output_dir = Path("data_folder/output/tailored_materials")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_tailored_application_package(self, job_title: str, company: str, job_description: str) -> Dict[str, Any]:
        """
        Creates custom bullet points and a targeted, forward-looking cover letter.
        """
        logger.info(f"[ResumeTailor] Tailoring application package for '{job_title}' at '{company}'...")

        # 1. Generate tailored achievement bullets
        bullets = self.drafter_reviewer.generate_tailored_bullets(job_title, job_description)

        # 2. Generate forward-looking cover letter
        cover_letter = self._generate_cover_letter(job_title, company, job_description, bullets)

        # 3. Save tailored cover letter to file
        safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
        cover_letter_file = self.output_dir / f"{safe_company}_Cover_Letter.txt"
        with open(cover_letter_file, "w", encoding="utf-8") as f:
            f.write(cover_letter)

        return {
            "job_title": job_title,
            "company": company,
            "tailored_bullets": bullets,
            "cover_letter_path": str(cover_letter_file),
            "cover_letter_text": cover_letter
        }

    def _generate_cover_letter(self, job_title: str, company: str, job_description: str, bullets: list) -> str:
        """
        Constructs a concise, 3-paragraph forward-looking cover letter.
        """
        bullet_str = "\n".join([f"• {b}" for b in bullets])
        
        letter = (
            f"Meeran Ahmed R.\n"
            f"Full Stack Developer | Chennai, India\n"
            f"Email: meeranahmed17@gmail.com | Phone: +91 8015186448\n"
            f"Portfolio: https://meeran-portfolio.antideploy.app | GitHub: https://github.com/Meeran-Ahmed\n\n"
            f"Dear Hiring Team at {company},\n\n"
            f"I am writing to express my strong enthusiasm for the {job_title} role at {company}. "
            f"With hands-on experience building production full stack applications with React, TypeScript, Python (FastAPI/Django), "
            f"and PostgreSQL, I specialize in shipping responsive, high-performance web systems and resilient APIs.\n\n"
            f"Here is how my recent technical work directly aligns with your current requirements:\n"
            f"{bullet_str}\n\n"
            f"I admire {company}'s focus on engineering excellence and user impact. In this role, my priority will be to integrate seamlessly with your team, "
            f"contribute clean, testable code, and help accelerate product delivery from day one. I welcome the opportunity to discuss how my skillset can support your engineering roadmap.\n\n"
            f"Thank you for your time and consideration.\n\n"
            f"Sincerely,\n"
            f"Meeran Ahmed R.\n"
        )
        return letter
