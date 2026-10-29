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
            # 0. Ensure we are on the /application form page
            curr_url = self.driver.current_url
            if "jobs.ashbyhq.com" in curr_url and "/application" not in curr_url:
                try:
                    apply_btn = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/application')] | //button[contains(translate(., 'APPLY', 'apply'), 'apply')]")
                    if apply_btn:
                        self.driver.execute_script("arguments[0].click();", apply_btn[0])
                        time.sleep(2.5)
                    else:
                        self.driver.get(curr_url.rstrip('/') + '/application')
                        time.sleep(2.5)
                except Exception as e:
                    logger.debug(f"Ashby navigation to form note: {e}")

            # 1. Wait for Ashby application container to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form, [data-ashby-application-form], [class*='ashby'], input"))
            )

            pi = self.profile_data.get("personal_information", {})
            full_name = f"{pi.get('name', 'Meeran')} {pi.get('surname', 'Ahmed R.')}".strip()
            email = str(pi.get("email", "meeranahmed17@gmail.com")).strip()
            phone = str(pi.get("phone", "+91 8015186448")).strip()
            if not phone.startswith("+"):
                phone = f"+91 {phone}"
            portfolio = "https://meeran-portfolio.antideploy.app"
            github = str(pi.get("github", "https://github.com/meeranahmed")).strip()
            linkedin = str(pi.get("linkedin", "https://www.linkedin.com/in/meeran-ahmed-r/")).strip()

            # 2. Upload Resume
            if self.resume_path:
                try:
                    file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                    if file_inputs:
                        file_inputs[0].send_keys(self.resume_path)
                        logger.info(f"Uploaded resume to Ashby: {self.resume_path}")
                        time.sleep(3.5)
                except Exception as e:
                    logger.debug(f"Ashby resume upload note: {e}")

            # 3. Direct System Field Population
            try:
                name_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[name='_systemfield_name']")
                if name_inputs and not name_inputs[0].get_attribute("value"):
                    name_inputs[0].clear()
                    name_inputs[0].send_keys(full_name)
                    logger.info(f"Filled Ashby system name: {full_name}")

                email_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[name='_systemfield_email']")
                if email_inputs and not email_inputs[0].get_attribute("value"):
                    email_inputs[0].clear()
                    email_inputs[0].send_keys(email)
                    logger.info(f"Filled Ashby system email: {email}")
            except Exception as e:
                logger.debug(f"System field note: {e}")

            # 4. Fill All Other Text & URL Inputs
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[type='tel'], input:not([type])")
            for inp in inputs:
                try:
                    if not inp.is_displayed() or not inp.is_enabled():
                        continue
                    curr = (inp.get_attribute("value") or "").strip()
                    if curr:
                        continue

                    name_attr = (inp.get_attribute("name") or "").lower()
                    label = self._get_label_for_element(inp)
                    combined = f"{name_attr} {label}"
                    val_to_fill = None

                    if ("name" in combined or "first" in combined) and "company" not in combined:
                        val_to_fill = full_name
                    elif "email" in combined:
                        val_to_fill = email
                    elif any(k in combined for k in ["phone", "mobile", "tel"]):
                        val_to_fill = phone
                    elif "linkedin" in combined:
                        val_to_fill = linkedin
                    elif "github" in combined:
                        val_to_fill = github
                    elif any(k in combined for k in ["portfolio", "website", "url", "link"]):
                        val_to_fill = portfolio
                    elif any(k in combined for k in ["city", "location", "address"]):
                        val_to_fill = "Bengaluru, India"

                    if val_to_fill:
                        inp.clear()
                        inp.send_keys(val_to_fill)
                        logger.info(f"Filled field ({combined[:30]}): {val_to_fill}")
                        time.sleep(0.2)
                except Exception:
                    pass

            # 5. Fill Textareas (custom questions / essays)
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            for ta in textareas:
                try:
                    if ta.is_displayed():
                        name_attr = (ta.get_attribute("name") or "").lower()
                        if "recaptcha" in name_attr:
                            continue
                        curr = (ta.get_attribute("value") or "").strip()
                        if not curr:
                            label = self._get_label_for_element(ta)
                            ans = f"As a Full Stack Developer with experience in React, Node.js, TypeScript, PostgreSQL, and Python, I build scalable web applications and high-performance APIs. I am very excited about {company} and the {job_title} role."
                            ta.send_keys(ans)
                            time.sleep(0.3)
                except Exception:
                    pass

            # 6. Check checkboxes & radios if present
            for cb in self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
                try:
                    if not cb.is_selected() and cb.is_displayed():
                        self.driver.execute_script("arguments[0].click();", cb)
                except Exception:
                    pass

            # 7. Take pre-submit snapshot for verification
            os.makedirs("data_folder/output/submissions", exist_ok=True)
            pre_snap = f"data_folder/output/submissions/pre_{company.lower().replace(' ', '_')}_{int(time.time())}.png"
            self.driver.save_screenshot(pre_snap)
            logger.info(f"Pre-submit screenshot saved: {pre_snap}")

            # 8. Submit
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)

            submit_btns = self.driver.find_elements(
                By.XPATH,
                "//button[contains(@class, 'ashby-application-form-submit-button')] | "
                "//button[contains(translate(., 'SUBMITAPPLY', 'submitapply'), 'submit application')] | "
                "//button[contains(translate(., 'SUBMITAPPLY', 'submitapply'), 'submit')] | "
                "//button[@type='submit']"
            )
            for btn in submit_btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(1)
                        self.driver.execute_script("arguments[0].click();", btn)
                        logger.info("Clicked Ashby Submit Application button!")
                        time.sleep(5)

                        after_url = self.driver.current_url.lower()
                        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                        success_keywords = ["thank you for applying", "application submitted", "received your application", "thanks for applying", "application received"]

                        post_snap = f"data_folder/output/submissions/post_{company.lower().replace(' ', '_')}_{int(time.time())}.png"
                        self.driver.save_screenshot(post_snap)
                        logger.info(f"Post-submit screenshot saved: {post_snap}")

                        if any(kw in page_text for kw in success_keywords) or any(p in after_url for p in ["/thanks", "/confirmation", "/applied"]):
                            logger.info(f"[Ashby] VERIFIED SUCCESS: Application confirmation detected for {company}!")
                            return True

                        has_errors = bool(self.driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(text(), 'This field is required')]"))
                        if has_errors:
                            logger.warning("[Ashby] Form blocked: required fields missing.")
                            return False
                        elif "/application" in after_url:
                            # Check if the submit button changed to Submitted / Success
                            if "submitted" in btn.text.lower() or "success" in page_text:
                                logger.info(f"[Ashby] Verified submission via button state for {company}!")
                                return True
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
            parent = element.find_element(By.XPATH, "ancestor::div[contains(@class, 'field') or contains(@class, 'form') or contains(@class, 'Container') or contains(@class, 'question') or contains(@class, 'Field')]")
            labels = parent.find_elements(By.TAG_NAME, "label")
            if labels and labels[0].text.strip():
                return labels[0].text.lower()
        except Exception:
            pass
        try:
            prec = element.find_elements(By.XPATH, "preceding-sibling::label | ../preceding-sibling::div//label")
            if prec and prec[-1].text.strip():
                return prec[-1].text.lower()
        except Exception:
            pass
        return (element.get_attribute("name") or element.get_attribute("aria-label") or element.get_attribute("placeholder") or "").lower()
