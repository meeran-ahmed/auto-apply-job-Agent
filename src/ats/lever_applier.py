import os
import time
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LeverApplier:
    def __init__(self, driver, resume_path: str, profile_data: dict, gpt_answerer=None):
        self.driver = driver
        self.resume_path = os.path.abspath(resume_path) if resume_path and os.path.exists(resume_path) else None
        self.profile_data = profile_data or {}
        self.gpt_answerer = gpt_answerer

    def apply(self, job_title: str = "", company: str = "") -> bool:
        logger.info(f"Starting Lever application for '{job_title}' at '{company}'...")
        try:
            # 1. If on job description page, click 'Apply for this job' button
            curr_url = self.driver.current_url.lower()
            if not curr_url.endswith("/apply"):
                apply_links = self.driver.find_elements(By.CSS_SELECTOR, "a.postings-btn, a[href*='/apply']")
                if apply_links:
                    self.driver.execute_script("arguments[0].click();", apply_links[0])
                    time.sleep(2.5)

            # 2. Wait for application form
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form#application-form, form.application-form, form"))
            )

            pi = self.profile_data.get("personal_information", {})
            full_name = f"{pi.get('name', 'Meeran')} {pi.get('surname', 'Ahmed R.')}".strip()
            email = str(pi.get("email", "meeranahmed17@gmail.com")).strip()
            phone = str(pi.get("phone", "8015186448")).strip()
            portfolio = "https://meeran-portfolio.antideploy.app"
            github = str(pi.get("github", "https://github.com/meeranahmed")).strip()
            linkedin = str(pi.get("linkedin", "https://www.linkedin.com/in/meeran-ahmed-r/")).strip()

            # 3. Fill Core Standard Inputs
            self._fill_named_input("name", full_name)
            self._fill_named_input("email", email)
            self._fill_named_input("phone", phone)
            self._fill_named_input("org", "Freelance Full Stack Developer")

            # 4. Fill Social / URL Inputs
            self._fill_named_input("urls[LinkedIn]", linkedin)
            self._fill_named_input("urls[GitHub]", github)
            self._fill_named_input("urls[Portfolio]", portfolio)
            self._fill_named_input("urls[Other]", portfolio)

            # 5. Upload Resume
            if self.resume_path:
                try:
                    file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file'][name='resume'], input[type='file']")
                    file_input.send_keys(self.resume_path)
                    logger.info(f"Uploaded resume to Lever: {self.resume_path}")
                    time.sleep(2.5)
                except Exception as e:
                    logger.debug(f"Lever resume upload note: {e}")

            # 6. Fill Additional Questions & Textareas
            textareas = self.driver.find_elements(By.CSS_SELECTOR, "textarea")
            for ta in textareas:
                try:
                    if ta.is_displayed():
                        curr = (ta.get_attribute("value") or "").strip()
                        if not curr:
                            label = self._get_label_for_element(ta)
                            ans = self._generate_answer(label, job_title)
                            ta.send_keys(ans)
                            time.sleep(0.5)
                except Exception:
                    pass

            # 7. Select radio buttons (e.g. Yes/No questions)
            radio_groups = self.driver.find_elements(By.CSS_SELECTOR, "ul.application-radios, div.application-field")
            for rg in radio_groups:
                try:
                    radios = rg.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                    if radios and not any(r.is_selected() for r in radios):
                        # Pick Yes if available, else first
                        picked = False
                        for r in radios:
                            r_label = r.find_element(By.XPATH, "..").text.lower()
                            if "yes" in r_label or "authorized" in r_label:
                                self.driver.execute_script("arguments[0].click();", r)
                                picked = True
                                break
                        if not picked:
                            self.driver.execute_script("arguments[0].click();", radios[0])
                except Exception:
                    pass

            # 8. Check consent/terms checkboxes
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            for cb in checkboxes:
                try:
                    if not cb.is_selected() and cb.is_displayed():
                        self.driver.execute_script("arguments[0].click();", cb)
                except Exception:
                    pass

            # 9. Submit Application
            time.sleep(2)
            submit_btn = self.driver.find_elements(By.CSS_SELECTOR, "button#btn-submit, button.template-btn-submit, button[type='submit']")
            if submit_btn:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn[0])
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", submit_btn[0])
                logger.info("Clicked Lever Submit button!")
                time.sleep(4)

                after_url = self.driver.current_url.lower()
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                success_keywords = ["thank you for applying", "application submitted", "received your application", "thanks for applying"]

                if any(kw in page_text for kw in success_keywords) or any(p in after_url for p in ["/thanks", "/confirmation", "/applied"]):
                    logger.info("[Lever] VERIFIED SUCCESS: Application confirmation detected!")
                    return True

                has_captcha = bool(self.driver.find_elements(By.XPATH, "//iframe[contains(@src, 'recaptcha') or contains(@src, 'hcaptcha')]"))
                if has_captcha:
                    logger.warning("[Lever] Form blocked by Google reCAPTCHA / hCaptcha verification.")
                    return False
                elif "/apply" in after_url:
                    logger.warning("[Lever] Form did not transition to confirmation page. Required fields or verification missing.")
                    return False
                return True

            logger.warning("No clickable Lever submit button found.")
            return False

        except Exception as e:
            logger.error(f"Error applying on Lever: {e}")
            return False

    def _fill_named_input(self, name: str, value: str):
        try:
            inputs = self.driver.find_elements(By.CSS_SELECTOR, f"input[name='{name}']")
            for inp in inputs:
                if inp.is_displayed() and inp.is_enabled():
                    curr = (inp.get_attribute("value") or "").strip()
                    if not curr:
                        inp.clear()
                        inp.send_keys(value)
        except Exception:
            pass

    def _get_label_for_element(self, element) -> str:
        try:
            parent = element.find_element(By.XPATH, "ancestor::div[contains(@class, 'application-field')]")
            labels = parent.find_elements(By.CSS_SELECTOR, ".application-label, label")
            if labels:
                return labels[0].text.lower()
        except Exception:
            pass
        return (element.get_attribute("placeholder") or element.get_attribute("name") or "").lower()

    def _generate_answer(self, question: str, job_title: str) -> str:
        if self.gpt_answerer:
            try:
                ans = self.gpt_answerer.answer_question_textual_wide_range(question)
                if ans and len(ans) > 3:
                    return ans
            except Exception:
                pass
        q = (question or "").lower()
        if any(w in q for w in ["notice", "start", "availability"]):
            return "Immediate (0 days notice)."
        if any(w in q for w in ["salary", "compensation", "ctc"]):
            return "Negotiable based on company standards."
        if any(w in q for w in ["implementation", "fde", "forward", "deploy", "onboarding"]):
            return "As an Implementation Executive at Pathfinder Enterprises Solutions, I specialized in deploying AI software solutions, onboarding clients, and integrating payment systems."
        if any(w in q for w in ["vibe", "ai", "claude", "cursor"]):
            return "I build rapid full-stack applications leveraging modern AI-assisted engineering tools like Cursor, Claude Code, and LLMs."
        return f"With over 2 years of experience building modern web platforms in React, Node.js, and TypeScript, I am fully equipped to drive high impact in the {job_title} role."
