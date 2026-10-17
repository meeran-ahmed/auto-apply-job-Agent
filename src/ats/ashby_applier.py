import os
import time
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class AshbyApplier:
    def __init__(self, driver, resume_path: str, profile_data: dict, gpt_answerer=None):
        self.driver = driver
        self.resume_path = os.path.abspath(resume_path) if resume_path and os.path.exists(resume_path) else None
        self.profile_data = profile_data or {}
        self.gpt_answerer = gpt_answerer

    def apply(self, job_title: str = "", company: str = "") -> bool:
        logger.info(f"Starting Ashby application for '{job_title}' at '{company}'...")
        try:
            # 1. Wait for Ashby application container to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form, [data-ashby-application-form], [class*='ashby']"))
            )

            pi = self.profile_data.get("personal_information", {})
            full_name = f"{pi.get('name', 'Meeran')} {pi.get('surname', 'Ahmed R.')}".strip()
            email = str(pi.get("email", "meeranahmed17@gmail.com")).strip()
            phone = str(pi.get("phone", "8015186448")).strip()
            portfolio = "https://meeran-portfolio.antideploy.app"
            github = str(pi.get("github", "https://github.com/meeranahmed")).strip()
            linkedin = str(pi.get("linkedin", "https://www.linkedin.com/in/meeran-ahmed-r/")).strip()

            # 2. Upload Resume first
            if self.resume_path:
                try:
                    file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                    if file_inputs:
                        file_inputs[0].send_keys(self.resume_path)
                        logger.info(f"Uploaded resume to Ashby: {self.resume_path}")
                        time.sleep(2.5)
                except Exception as e:
                    logger.debug(f"Ashby resume upload note: {e}")

            # 3. Fill All Text & URL Inputs
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[type='tel'], input:not([type])")
            for inp in inputs:
                try:
                    if not inp.is_displayed() or not inp.is_enabled():
                        continue
                    curr = (inp.get_attribute("value") or "").strip()
                    if curr:
                        continue

                    label = self._get_label_for_element(inp)
                    val_to_fill = None

                    if "name" in label and "company" not in label:
                        val_to_fill = full_name
                    elif "email" in label:
                        val_to_fill = email
                    elif any(k in label for k in ["phone", "mobile"]):
                        val_to_fill = phone
                    elif "linkedin" in label:
                        val_to_fill = linkedin
                    elif "github" in label:
                        val_to_fill = github
                    elif any(k in label for k in ["portfolio", "website", "url"]):
                        val_to_fill = portfolio
                    elif "city" in label or "location" in label:
                        val_to_fill = "Vaniyambadi, Tamil Nadu, India"

                    if val_to_fill:
                        inp.clear()
                        inp.send_keys(val_to_fill)
                        time.sleep(0.2)
                except Exception:
                    pass

            # 4. Fill Textareas (custom questions / essays)
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            for ta in textareas:
                try:
                    if ta.is_displayed():
                        curr = (ta.get_attribute("value") or "").strip()
                        if not curr:
                            label = self._get_label_for_element(ta)
                            ans = f"As a Full Stack Developer with over 2 years of experience in React, Node.js, and TypeScript, I am eager to apply for the {job_title} role."
                            ta.send_keys(ans)
                            time.sleep(0.3)
                except Exception:
                    pass

            # 5. Check checkboxes & radios
            for cb in self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
                try:
                    if not cb.is_selected() and cb.is_displayed():
                        self.driver.execute_script("arguments[0].click();", cb)
                except Exception:
                    pass

            # 6. Submit
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)

            submit_btns = self.driver.find_elements(
                By.XPATH,
                "//button[contains(translate(., 'SUBMITAPPLY', 'submitapply'), 'submit') or contains(translate(., 'SUBMITAPPLY', 'submitapply'), 'apply') or contains(translate(., 'SEND', 'send'), 'send')] | "
                "//button[@type='submit'] | "
                "//input[@type='submit'] | "
                "//button[contains(@class, 'submit') or contains(@class, 'apply')]"
            )
            for btn in submit_btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(1)
                        self.driver.execute_script("arguments[0].click();", btn)
                        logger.info("Clicked Ashby / Universal Submit button!")
                        time.sleep(4)

                        after_url = self.driver.current_url.lower()
                        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                        success_keywords = ["thank you for applying", "application submitted", "received your application", "thanks for applying"]

                        if any(kw in page_text for kw in success_keywords) or any(p in after_url for p in ["/thanks", "/confirmation", "/applied"]):
                            logger.info("[Ashby] VERIFIED SUCCESS: Application confirmation detected!")
                            return True

                        has_errors = bool(self.driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(text(), 'required')]"))
                        if has_errors:
                            logger.warning("[Ashby] Form blocked: required fields missing.")
                            return False
                        elif "/application" in after_url:
                            logger.warning("[Ashby] Form did not transition to confirmation.")
                            return False
                        return True
                except Exception:
                    continue

            return False

        except Exception as e:
            logger.error(f"Error applying on Ashby: {e}")
            return False

    def _get_label_for_element(self, element) -> str:
        try:
            parent = element.find_element(By.XPATH, "ancestor::div[contains(@class, 'field') or contains(@class, 'form')]")
            labels = parent.find_elements(By.TAG_NAME, "label")
            if labels:
                return labels[0].text.lower()
        except Exception:
            pass
        return (element.get_attribute("name") or element.get_attribute("aria-label") or element.get_attribute("placeholder") or "").lower()
