import os
import re
import time
from pathlib import Path
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class GreenhouseApplier:
    def __init__(self, driver, resume_path: str, profile_data: dict, gpt_answerer=None):
        self.driver = driver
        self.resume_path = os.path.abspath(resume_path) if resume_path and os.path.exists(resume_path) else None
        self.profile_data = profile_data or {}
        self.gpt_answerer = gpt_answerer

    def apply(self, job_title: str = "", company: str = "") -> bool:
        logger.info(f"Starting Greenhouse application for '{job_title}' at '{company}'...")
        try:
            # 1. Wait for form to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form#application_form, #apply_form, form"))
            )

            pi = self.profile_data.get("personal_information", {})
            first_name = str(pi.get("name", "Meeran")).strip()
            last_name = str(pi.get("surname", "Ahmed R.")).strip()
            full_name = f"{first_name} {last_name}".strip()
            email = str(pi.get("email", "meeranahmed17@gmail.com")).strip()
            phone = str(pi.get("phone", "8015186448")).strip()
            city = str(pi.get("city", "Vaniyambadi")).strip()
            portfolio = "https://meeran-portfolio.antideploy.app"
            github = str(pi.get("github", "https://github.com/meeranahmed")).strip()
            linkedin = str(pi.get("linkedin", "https://www.linkedin.com/in/meeran-ahmed-r/")).strip()

            # 2. Fill standard personal fields
            self._fill_field(["first_name", "first-name", "fname"], first_name)
            self._fill_field(["last_name", "last-name", "lname"], last_name)
            self._fill_field(["name", "full_name", "full-name"], full_name)
            self._fill_field(["email"], email)
            self._fill_field(["phone", "cell", "mobile"], phone)

            # Location / City
            self._fill_field(["location", "city"], f"{city}, Tamil Nadu, India")

            # 3. Upload Resume
            if self.resume_path:
                try:
                    file_inputs = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        "input[type='file'][id*='resume'], input[type='file'][name*='resume'], input[type='file']"
                    )
                    for fi in file_inputs:
                        if fi.is_enabled():
                            fi.send_keys(self.resume_path)
                            logger.info(f"Uploaded resume to Greenhouse: {self.resume_path}")
                            time.sleep(2)
                            break
                except Exception as e:
                    logger.debug(f"Resume upload note: {e}")

            # 4. Fill Links (LinkedIn, Portfolio, GitHub)
            all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='url'], input:not([type])")
            for inp in all_inputs:
                try:
                    label = self._get_label_for_element(inp)
                    val = (inp.get_attribute("value") or "").strip()
                    if not val:
                        if "linkedin" in label:
                            inp.send_keys(linkedin)
                        elif any(k in label for k in ["portfolio", "website", "personal link", "project"]):
                            inp.send_keys(portfolio)
                        elif "github" in label:
                            inp.send_keys(github)
                except Exception:
                    pass

            # 5. Handle Dropdowns / Selects (Authorizations, Demographics, etc.)
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            for sel_el in selects:
                try:
                    if not sel_el.is_displayed():
                        continue
                    select = Select(sel_el)
                    current_val = select.first_selected_option.text.strip().lower() if select.all_selected_options else ""
                    if current_val and not any(p in current_val for p in ["select", "choose", "please"]):
                        continue

                    label = self._get_label_for_element(sel_el)
                    matched = False
                    for opt in select.options:
                        ot = opt.text.lower()
                        # Visa / Legal authorization
                        if "authorized" in label or "legally" in label:
                            if "yes" in ot or "authorized" in ot:
                                select.select_by_visible_text(opt.text)
                                matched = True
                                break
                        elif "sponsorship" in label or "require" in label:
                            if "yes" in ot:
                                select.select_by_visible_text(opt.text)
                                matched = True
                                break
                        elif "gender" in label:
                            if "male" in ot:
                                select.select_by_visible_text(opt.text)
                                matched = True
                                break
                        elif "yes" in ot:
                            select.select_by_visible_text(opt.text)
                            matched = True
                            break

                    if not matched and len(select.options) > 1:
                        for opt in select.options[1:]:
                            if opt.text.strip() and not any(p in opt.text.lower() for p in ["select", "choose"]):
                                select.select_by_visible_text(opt.text)
                                break
                except Exception:
                    pass

            # 6. Handle custom textareas & remaining questions
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            for ta in textareas:
                try:
                    if not ta.is_displayed():
                        continue
                    curr_text = (ta.get_attribute("value") or "").strip()
                    if not curr_text:
                        label = self._get_label_for_element(ta)
                        answer = self._generate_answer(label, job_title)
                        ta.send_keys(answer)
                        time.sleep(0.5)
                except Exception:
                    pass

            # 7. Submit Application
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)

            submit_elements = self.driver.find_elements(
                By.XPATH,
                "//button[contains(translate(., 'SUBMITAPPLY', 'submitapply'), 'submit') or contains(translate(., 'SUBMITAPPLY', 'submitapply'), 'apply') or contains(translate(., 'SEND', 'send'), 'send')] | "
                "//input[@type='submit'] | "
                "//input[contains(@value, 'Submit') or contains(@value, 'Apply')] | "
                "//button[@type='submit'] | "
                "//button[contains(@id, 'submit') or contains(@class, 'submit')] | "
                "//a[contains(@class, 'submit') or contains(@class, 'apply') and contains(@role, 'button')]"
            )
            for btn in submit_elements:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(1)
                        self.driver.execute_script("arguments[0].click();", btn)
                        logger.info("Clicked Greenhouse / Universal Submit button!")
                        time.sleep(4)
                        return True
                except Exception:
                    continue

            logger.warning("No clickable Greenhouse submit button found.")
            return False

        except Exception as e:
            logger.error(f"Error applying on Greenhouse: {e}")
            return False

    def _fill_field(self, name_variants: list, value: str):
        for name in name_variants:
            selectors = [
                f"input#{name}",
                f"input[name='{name}']",
                f"input[name*='[{name}]']",
                f"input[id*='{name}']"
            ]
            for sel in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for el in elements:
                    if el.is_displayed() and el.is_enabled():
                        curr = (el.get_attribute("value") or "").strip()
                        if not curr:
                            el.clear()
                            el.send_keys(value)
                            return

    def _get_label_for_element(self, element) -> str:
        try:
            parent = element.find_element(By.XPATH, "ancestor::div[contains(@class, 'field') or contains(@class, 'form-group') or contains(@class, 'row')]")
            labels = parent.find_elements(By.TAG_NAME, "label")
            if labels:
                return labels[0].text.lower()
        except Exception:
            pass
        return (element.get_attribute("aria-label") or element.get_attribute("placeholder") or element.get_attribute("name") or element.get_attribute("id") or "").lower()

    def _generate_answer(self, question: str, job_title: str) -> str:
        if self.gpt_answerer:
            try:
                ans = self.gpt_answerer.answer_question_textual_wide_range(question)
                if ans and len(ans) > 3:
                    return ans
            except Exception:
                pass

        q = question.lower()
        if any(w in q for w in ["why", "interest", "reason", "cover letter"]):
            return (
                f"I am deeply excited to apply for the {job_title} role. With over 2 years of hands-on experience "
                "architecting production full-stack web platforms using React, Node.js, and TypeScript, I have built "
                "scalable multi-tenant solutions like Kamyaab Academy and Vexa AI. I look forward to contributing "
                "high-performance, reliable code to your team."
            )
        if any(w in q for w in ["project", "achievement", "proud"]):
            return (
                "One of my most notable achievements was architecting Kamyaab Academy, an educational platform "
                "supporting 1,000+ active users. I implemented a robust 3-tier architecture with PostgreSQL, "
                "Google OAuth 2.0, and payment gateway integrations, achieving sub-second API latencies."
            )
        return "Yes, fully experienced and aligned with the role requirements."
