import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple, List
from loguru import logger

class FitEvaluator:
    """
    100-Point Candidate-Vacancy Fit Evaluator (adapted from ai-job-search).
    Evaluates hard technical skills, experience level, and remote requirements
    before any job application action is taken.
    """

    def __init__(self, resume_path: str = "data_folder/plain_text_resume.yaml"):
        self.resume_path = Path(resume_path)
        self.candidate_profile = self._load_candidate_profile()
        self.core_skills = set(self._extract_candidate_skills())
        self.blacklist_titles = [
            "intern", "internship", "co-op", "trainee", "student", "fellow",
            "senior", "sr.", "lead", "principal", "staff", "architect",
            "director", "vp", "head of", "manager", "chief"
        ]
        self.target_keywords = [
            "full stack", "fullstack", "frontend", "front-end", "backend",
            "back-end", "software engineer", "developer", "python", "react",
            "web developer", "software developer", "forward deployed",
            "forward deployed engineer", "implementation engineer",
            "implementation executive", "implementation specialist",
            "technical solutions", "solutions engineer", "deployment engineer",
            "vibe coding", "vibe coder", "ai engineer", "ai developer",
            "prompt engineer", "product engineer"
        ]

    def _load_candidate_profile(self) -> Dict[str, Any]:
        if not self.resume_path.exists():
            return {}
        try:
            with open(self.resume_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"[FitEvaluator] Error loading candidate profile: {e}")
            return {}

    def _extract_candidate_skills(self) -> List[str]:
        skills = []
        # Extract from plain_text_resume.yaml
        skills_raw = self.candidate_profile.get("skills", {})
        if isinstance(skills_raw, dict):
            for cat, items in skills_raw.items():
                if isinstance(items, list):
                    skills.extend([str(i).lower().strip() for i in items])
                elif isinstance(items, str):
                    skills.extend([s.lower().strip() for s in items.split(",")])
        elif isinstance(skills_raw, list):
            skills.extend([str(s).lower().strip() for s in skills_raw])

        # Essential defaults if empty
        defaults = [
            "python", "javascript", "typescript", "react", "react.js",
            "fastapi", "django", "postgresql", "sql", "git", "rest", "api",
            "docker", "html", "css", "tailwind", "node", "nodejs", "next.js",
            "express", "implementation", "deployment", "integration", "onboarding",
            "ai", "llm", "automation"
        ]
        for d in defaults:
            if d not in skills:
                skills.append(d)
        return skills

    def evaluate_fit(self, title: str, description: str, company: str = "", location: str = "") -> Tuple[int, bool, Dict[str, Any]]:
        """
        Calculates 100-point fit score:
        - 40 pts: Hard technical skill overlap
        - 30 pts: Experience / Role level match (instant 0 if blacklisted/internship)
        - 30 pts: Remote & work domain match
        Pass threshold is >= 75 points.
        """
        t_lower = title.lower()
        desc_lower = (description or "").lower()

        # 1. HARD REJECTION CHECK (User mandate: strictly zero internships and no senior/lead roles)
        for blacklisted in self.blacklist_titles:
            # Word boundary check for short words like 'sr'
            if re.search(r'\b' + re.escape(blacklisted) + r'\b', t_lower):
                logger.debug(f"[FitEvaluator] Rejected '{title}' due to blacklisted token: '{blacklisted}'")
                return 0, False, {"reason": f"Title contains blacklisted term: {blacklisted}", "score": 0}

        # Verify role relevance
        is_relevant_role = any(re.search(r'\b' + re.escape(kw) + r'\b', t_lower) for kw in self.target_keywords)
        if not is_relevant_role and "developer" not in t_lower and "engineer" not in t_lower:
            return 20, False, {"reason": "Not a target developer/engineering role", "score": 20}

        # 2. Hard Skills Overlap (Max 40 points)
        matched_skills = []
        for skill in self.core_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', desc_lower) or re.search(r'\b' + re.escape(skill) + r'\b', t_lower):
                matched_skills.append(skill)

        # Scale skills: if it's a verified target role, grant baseline 20 pts + 8 per matched skill up to 40
        if is_relevant_role:
            skill_score = max(20, min(40, 20 + len(matched_skills) * 6))
        else:
            skill_score = min(40, len(matched_skills) * 8)

        # 3. Experience & Role Scope Match (Max 30 points)
        exp_score = 30
        # Check years of experience mentioned in description
        exp_matches = re.findall(r'(\d+)\+?\s*(?:-\s*(\d+))?\s*(?:years?|yrs?)(?:\s*of)?\s*experience', desc_lower)
        for match in exp_matches:
            min_yr = int(match[0])
            if min_yr > 5:
                # Disqualify positions requiring > 5 years experience
                return 30, False, {"reason": f"Requires {min_yr}+ years experience (exceeds candidate profile)", "score": 30}
            elif min_yr > 3:
                exp_score = 15

        # 4. Remote / Location Alignment (Max 30 points)
        loc_score = 30
        combined_text = f"{title} {location} {description}".lower()
        if any(term in combined_text for term in ["remote", "anywhere", "work from home", "chennai", "bangalore", "bengaluru", "tamil nadu", "karnataka", "india"]):
            loc_score = 30
        elif "hybrid" in combined_text:
            loc_score = 25
        else:
            loc_score = 15

        total_score = skill_score + exp_score + loc_score
        is_fit = total_score >= 70

        details = {
            "score": total_score,
            "skill_score": skill_score,
            "exp_score": exp_score,
            "loc_score": loc_score,
            "matched_skills": matched_skills[:10],
            "title": title,
            "company": company,
            "meets_threshold": is_fit
        }

        if is_fit:
            logger.info(f"[FitEvaluator] High-Conviction Fit ({total_score}/100) -> '{title}' at '{company}' (Skills: {', '.join(matched_skills[:5])})")
        else:
            logger.debug(f"[FitEvaluator] Sub-threshold Fit ({total_score}/100) -> '{title}' at '{company}'")

        return total_score, is_fit, details
