import time
import urllib.parse
from loguru import logger
from selenium.webdriver.common.by import By
from src.core.stealth_driver import StealthDriver
from src.core.loop_guard import LoopGuard


class NaukriAgent:
    """
    Automates 1-click FastApply and Easy Apply on Naukri.com (India's premier tech portal)
    using the user's authenticated Chrome session.
    """

    def __init__(self, driver, gemini_answerer=None, reporter=None):
        self.driver = driver
        self.gemini_answerer = gemini_answerer
        self.reporter = reporter
        self.loop_guard = LoopGuard()

    def search_and_apply(self, keyword: str = "Full Stack Developer", max_jobs: int = 10) -> int:
        encoded_kw = urllib.parse.quote(keyword)
        # Search URL targeting remote/hybrid jobs
        search_url = f"https://www.naukri.com/{encoded_kw}-jobs?k={encoded_kw}&qcache=1&experience=1&experience=2"
        logger.info(f"[NaukriAgent] Navigating to Naukri search: {search_url}")
        
        self.driver.get(search_url)
        StealthDriver.random_sleep(3.0, 5.0)

        applied_count = 0
        job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.srp-jobtuple-wrapper, article.jobTuple, a.title")
        logger.info(f"[NaukriAgent] Found {len(job_cards)} job cards on page.")

        links = []
        for card in job_cards:
            try:
                a_tag = card if card.tag_name == "a" else card.find_element(By.CSS_SELECTOR, "a.title")
                href = a_tag.get_attribute("href")
                title = a_tag.text.strip()
                if href and self._is_target_role(title):
                    links.append((title, href))
            except Exception:
                continue

        logger.info(f"[NaukriAgent] Filtered {len(links)} matching candidate jobs (no internships/seniors).")

        for title, link in links:
            if applied_count >= max_jobs:
                break
            if self.reporter and self.reporter.is_already_applied(link, title):
                logger.info(f"[NaukriAgent] Already applied to '{title}', skipping...")
                continue
            try:
                success, company = self.apply_to_job(title, link)
                if success:
                    applied_count += 1
                    logger.info(f"[NaukriAgent] Successfully applied to '{title}' at '{company}' on Naukri ({applied_count}/{max_jobs})")
                    if self.reporter:
                        self.reporter.record_applied(title, company, "Naukri.com", link)
                StealthDriver.random_sleep(3.0, 6.0)
            except Exception as e:
                logger.error(f"[NaukriAgent] Error applying to {title}: {e}")

        return applied_count

    def apply_to_job(self, title: str, link: str):
        logger.info(f"[NaukriAgent] Opening job: {title} -> {link}")
        self.driver.get(link)
        StealthDriver.random_sleep(2.5, 4.0)

        # Extract company name
        company = "Naukri Hiring Company"
        comp_elems = self.driver.find_elements(By.CSS_SELECTOR, "a.comp-name, div.company-name, a[href*='cmp/'], a.top-company-name, div.jd-top-head")
        for ce in comp_elems:
            txt = ce.text.strip().split("\n")[0]
            if txt and txt.lower() not in ["to", "years", "reviews", "hiring company", "full stack developer"]:
                company = txt
                break

        if company == "Naukri Hiring Company" and "job-listings-" in link:
            slug = link.split("job-listings-")[-1].split("?")[0]
            tokens = slug.split("-")
            for i, tok in enumerate(tokens):
                if tok in ["chennai", "bengaluru", "bangalore", "noida", "mumbai", "hyderabad", "pune", "delhi", "remote", "mohali", "nashik", "gurgaon"]:
                    if i > 0 and tokens[i-1].lower() != "developer":
                        company = tokens[i-1].capitalize()
                    break

        # Look for 1-click apply button
        apply_buttons = self.driver.find_elements(
            By.XPATH,
            "//button[contains(text(), 'Apply') or contains(@id, 'apply-button') or contains(@class, 'apply')] | "
            "//a[contains(text(), 'Apply on Company Site') or contains(@class, 'apply-button')]"
        )

        if not apply_buttons:
            logger.warning(f"[NaukriAgent] No apply button found for '{title}' (already applied or closed).")
            return False, company

        btn = apply_buttons[0]
        StealthDriver.human_click(self.driver, btn)
        StealthDriver.random_sleep(2.5, 4.5)

        # Handle post-click chat or multi-step questions
        self._handle_screening_questions(title)

        return True, company

    def _handle_screening_questions(self, job_title: str):
        text_inputs = self.driver.find_elements(By.XPATH, "//input[@type='text' and not(@value)] | //textarea[not(text())]")
        for inp in text_inputs[:5]:
            try:
                if inp.is_displayed():
                    label = inp.get_attribute("placeholder") or "Experience"
                    answer = self.gemini_answerer.answer_question(label, job_title=job_title) if self.gemini_answerer else "3 years"
                    StealthDriver.human_type(inp, answer)
                    time.sleep(0.5)
            except Exception:
                pass

        submit_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Submit') or contains(text(), 'Save and Apply')]")
        if submit_btns:
            StealthDriver.human_click(self.driver, submit_btns[0])
            time.sleep(2)

    def _is_target_role(self, title: str) -> bool:
        t = title.lower()
        blacklist = ["intern", "internship", "senior", "sr.", "lead", "architect", "manager", "director", "head", "trainee"]
        if any(b in t for b in blacklist):
            return False
        keywords = ["developer", "engineer", "full stack", "frontend", "python", "react", "web", "software"]
        return any(k in t for k in keywords)
