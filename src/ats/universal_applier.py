import os
import time
import random
from typing import Dict, Any, Optional
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from src.core.stealth_engine import InvisibleDotsStealth
from src.llm.gemini_synthesizer import GeminiRecruiterSynthesizer


class UniversalATSApplier:
    """
    Universal Autonomous ATS Form Applier.
    Unified engine capable of handling Ashby, Greenhouse, Lever, and bespoke career portals.
    Incorporates Invisible Dots human-like interactions and Gemini-powered dynamic Q&A.
    """

    def __init__(self, driver: webdriver.Chrome, resume_path: str, profile_data: dict, synthesizer: Optional[GeminiRecruiterSynthesizer] = None):
        self.driver = driver
        self.resume_path = os.path.abspath(resume_path) if resume_path and os.path.exists(resume_path) else None
        self.profile = profile_data or {}
        self.synthesizer = synthesizer or GeminiRecruiterSynthesizer()

        # Extract core candidate details
        pi = self.profile.get("personal_information", {})
        self.first_name = str(pi.get("name", "Meeran")).strip()
        self.last_name = str(pi.get("surname", "Ahmed R.")).strip()
        self.full_name = f"{self.first_name} {self.last_name}".strip()
        self.email = str(pi.get("email", "meeranahmed17@gmail.com")).strip()
        self.phone = str(pi.get("phone", "+91 8015186448")).strip()
        self.city = str(pi.get("city", "Chennai")).strip()
        self.portfolio = "https://meeran-portfolio.antideploy.app"
        self.github = str(pi.get("github", "https://github.com/meeranahmed")).strip()
        self.linkedin = str(pi.get("linkedin", "https://www.linkedin.com/in/meeran-ahmed-r/")).strip()

    def apply(self, job_title: str, company: str, target_url: str) -> bool:
        """
        Main application submission pipeline with zero-false-positive verification.
        """
        logger.info(f"[UniversalApplier] Initiating stealth application for '{job_title}' at '{company}'...")
        try:
            self.driver.get(target_url)
            time.sleep(random.uniform(3.0, 4.5))

            # Handle intermediate apply buttons
            self._handle_pre_application_pages()

            # Identify platform architecture
            curr_url = self.driver.current_url.lower()
            logger.info(f"[UniversalApplier] Resolved form page: {curr_url}")

            # 1. Fill basic identity inputs
            self._fill_identity_fields()

            # 2. Upload Resume
            self._upload_resume()

            # 3. Fill URLs & Professional Profiles
            self._fill_profile_links()

            # 4. Handle Platform Dropdowns (React-Select, Ashby selects, Native HTML selects)
            self._fill_dropdowns()

            # 5. Handle Recruiter Custom Questions & Textareas via Gemini Synthesizer
            self._fill_custom_questions(job_title, company)

            # 6. Check Mandatory Consent / Compliance Checkboxes
            self._check_compliance_boxes()

            # 7. Pre-submit screenshot
            os.makedirs("data_folder/output/submissions", exist_ok=True)
            shot_pre = f"data_folder/output/submissions/pre_{company.lower().replace(' ', '_')}_{int(time.time())}.png"
            self.driver.save_screenshot(shot_pre)

            # 8. Humanized Submit Action & Self-Healing
            success = self._execute_submit_and_verify(job_title, company)
            return success

        except Exception as e:
            logger.error(f"[UniversalApplier] Exception during application run: {e}")
            return False

    def _handle_pre_application_pages(self):
        """Clicks 'Apply for this job' or navigates directly to the application container."""
        try:
            curr = self.driver.current_url.lower()
            if "ashbyhq.com" in curr and "/application" not in curr:
                apply_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/application')] | //button[contains(translate(., 'APPLY', 'apply'), 'apply')]")
                if apply_links:
                    InvisibleDotsStealth.human_move_and_click(self.driver, apply_links[0])
                    time.sleep(2.5)

            if "lever.co" in curr and not curr.endswith("/apply"):
                apply_links = self.driver.find_elements(By.CSS_SELECTOR, "a.postings-btn, a[href*='/apply']")
                if apply_links:
                    InvisibleDotsStealth.human_move_and_click(self.driver, apply_links[0])
                    time.sleep(2.5)
        except Exception as e:
            logger.debug(f"Pre-apply step note: {e}")

    def _fill_identity_fields(self):
        """Fills First Name, Last Name, Full Name, Email, and Phone."""
        field_mappings = [
            (["first_name", "first-name", "fname", "given-name"], self.first_name),
            (["last_name", "last-name", "lname", "family-name"], self.last_name),
            (["name", "full_name", "full-name", "_systemfield_name"], self.full_name),
            (["email", "_systemfield_email"], self.email),
            (["phone", "cell", "mobile", "tel", "_systemfield_phone"], self.phone),
            (["candidate-location", "city", "location"], "Chennai, India")
        ]

        for keys, val in field_mappings:
            for k in keys:
                selectors = [
                    f"input#{k}", f"input[name='{k}']", f"input[id*='{k}']",
                    f"input[name*='{k}']", f"input[placeholder*='{k}']"
                ]
                for sel in selectors:
                    for el in self.driver.find_elements(By.CSS_SELECTOR, sel):
                        try:
                            if el.is_displayed() and el.is_enabled():
                                curr = (el.get_attribute("value") or "").strip()
                                if not curr:
                                    InvisibleDotsStealth.human_type(self.driver, el, val)
                                    logger.info(f"Filled identity input [{k}]: {val}")
                        except Exception:
                            pass

    def _upload_resume(self):
        """Locates and uploads resume PDF."""
        if not self.resume_path:
            return
        try:
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            for fi in file_inputs:
                try:
                    fi.send_keys(self.resume_path)
                    logger.info(f"Uploaded resume file: {self.resume_path}")
                    time.sleep(2.5)
                    break
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Resume upload note: {e}")

    def _fill_profile_links(self):
        """Fills LinkedIn, Portfolio, and GitHub profile links."""
        inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='url'], input:not([type])")
        for inp in inputs:
            try:
                if not inp.is_displayed():
                    continue
                curr = (inp.get_attribute("value") or "").strip()
                if curr:
                    continue

                label = self._get_label_for_element(inp).lower()
                name_attr = (inp.get_attribute("name") or "").lower()
                combined = f"{label} {name_attr}"

                if "linkedin" in combined:
                    InvisibleDotsStealth.human_type(self.driver, inp, self.linkedin)
                    logger.info("Filled LinkedIn profile.")
                elif any(w in combined for w in ["portfolio", "website", "personal link", "project url"]):
                    InvisibleDotsStealth.human_type(self.driver, inp, self.portfolio)
                    logger.info("Filled Portfolio website.")
                elif "github" in combined:
                    InvisibleDotsStealth.human_type(self.driver, inp, self.github)
                    logger.info("Filled GitHub profile.")
            except Exception:
                pass

    def _fill_dropdowns(self):
        """Handles React-Select shells, Ashby comboboxes, and native HTML selects."""
        # 1. React-Select inputs (mapped by label[for])
        labels = self.driver.find_elements(By.TAG_NAME, "label")
        for lbl in labels:
            try:
                for_id = lbl.get_attribute("for")
                lt = lbl.text.strip().lower()
                if not for_id or not lt:
                    continue

                target_inputs = self.driver.find_elements(By.ID, for_id)
                if not target_inputs:
                    continue
                inp = target_inputs[0]

                role = inp.get_attribute("role") or ""
                classes = inp.get_attribute("class") or ""
                if role == "combobox" or "select__input" in classes:
                    val_to_select = self._determine_dropdown_value(lt)
                    if val_to_select:
                        inp.send_keys(val_to_select)
                        time.sleep(0.6)
                        inp.send_keys(Keys.ENTER)
                        inp.send_keys(Keys.ESCAPE)
                        logger.info(f"Selected [{lt[:30]}]: {val_to_select}")
            except Exception:
                continue

        # 2. Native HTML Select tags
        selects = self.driver.find_elements(By.TAG_NAME, "select")
        for sel in selects:
            try:
                if not sel.is_displayed():
                    continue
                s = Select(sel)
                lbl = self._get_label_for_element(sel).lower()
                desired = self._determine_dropdown_value(lbl)
                for opt in s.options:
                    if desired.lower() in opt.text.lower():
                        s.select_by_visible_text(opt.text)
                        break
            except Exception:
                pass

    def _determine_dropdown_value(self, label: str) -> str:
        """Determines best standard value for common ATS dropdown options."""
        l = label.lower()
        if "country" in l or "residence" in l or "location" in l:
            return "India"
        if "gender" in l:
            return "Male"
        if "language" in l:
            return "English"
        if any(w in l for w in ["hispanic", "latino"]):
            return "No"
        if "veteran" in l:
            return "I am not a protected veteran"
        if any(w in l for w in ["disability", "handicap"]):
            return "No"
        if any(w in l for w in ["authorized", "legally eligible", "authorization", "evidence"]):
            return "Yes"
        if any(w in l for w in ["sponsorship", "require visa", "sponsor", "require"]):
            return "No"
        if any(w in l for w in ["pronoun"]):
            return "He/Him"
        if any(w in l for w in ["hear about", "source"]):
            return "LinkedIn"
        if any(w in l for w in ["policy", "consent", "agree", "terms"]):
            return "Yes"
        return "Yes"

    def _fill_custom_questions(self, job_title: str, company: str):
        """Leverages Gemini Neural Synthesizer for textareas and open recruiter questions."""
        textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
        for ta in textareas:
            try:
                if not ta.is_displayed():
                    continue
                curr = (ta.get_attribute("value") or "").strip()
                if curr:
                    continue

                q_label = self._get_label_for_element(ta)
                answer = self.synthesizer.synthesize_answer(q_label, job_title, company)
                InvisibleDotsStealth.human_type(self.driver, ta, answer)
                logger.info(f"Synthesized recruiter answer for [{q_label[:30]}]: {answer[:60]}...")
            except Exception:
                pass

        # Handle Ashby and general radio options for sponsorship, authorization, etc.
        for radio in self.driver.find_elements(By.XPATH, "//input[@type='radio'] | //div[@role='radio']"):
            try:
                label_text = self._get_label_for_element(radio).lower()
                r_val = (radio.get_attribute("value") or radio.text or "").lower()
                if "sponsor" in label_text:
                    if "no" in r_val:
                        InvisibleDotsStealth.human_move_and_click(self.driver, radio)
                elif "authorized" in label_text or "eligible" in label_text:
                    if "yes" in r_val:
                        InvisibleDotsStealth.human_move_and_click(self.driver, radio)
            except Exception:
                pass

    def _check_compliance_boxes(self):
        """Auto-checks mandatory compliance, GDPR, and data policy checkboxes."""
        checkboxes = self.driver.find_elements(By.XPATH, "//input[@type='checkbox']")
        for cb in checkboxes:
            try:
                if not cb.is_selected():
                    InvisibleDotsStealth.human_move_and_click(self.driver, cb)
                    logger.info("Checked compliance checkbox.")
            except Exception:
                pass

    def _execute_submit_and_verify(self, job_title: str, company: str) -> bool:
        """Finds submit button, executes Bézier click, and verifies terminal confirmation."""
        submit_selectors = [
            "//button[contains(translate(., 'SUBMITAPPLY', 'submitapply'), 'submit application')]",
            "//button[contains(translate(., 'SUBMITAPPLY', 'submitapply'), 'submit')]",
            "//button[contains(translate(., 'APPLY', 'apply'), 'apply')]",
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//button[contains(@class, 'ashby-application-form-submit-button')]"
        ]

        for sel in submit_selectors:
            buttons = self.driver.find_elements(By.XPATH, sel)
            for btn in buttons:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        logger.info(f"Clicking Submit button for '{job_title}' at '{company}'...")
                        InvisibleDotsStealth.human_move_and_click(self.driver, btn)
                        time.sleep(random.uniform(7.0, 9.0))

                        # Comprehensive Verification Markers
                        after_url = self.driver.current_url.lower()
                        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                        
                        success_markers = [
                            "successfully submitted",
                            "application was successfully submitted",
                            "your application was successfully submitted",
                            "thank you for applying",
                            "application submitted", 
                            "application received",
                            "received your application",
                            "thanks for applying",
                            "we'll contact you if there are next steps",
                            "thank you for your interest"
                        ]

                        shot_post = f"data_folder/output/submissions/post_{company.lower().replace(' ', '_')}_{int(time.time())}.png"
                        self.driver.save_screenshot(shot_post)

                        # Check for success indicators
                        if any(marker in page_text for marker in success_markers) or any(p in after_url for p in ["/confirmation", "/thanks", "/applied", "/success"]):
                            logger.info(f"[UniversalApplier] ✅ VERIFIED TERMINAL SUCCESS: Application confirmed for '{company}'!")
                            return True

                        # Self-Healing: Check if Ashby flagged missing required fields
                        error_links = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'Error')]//a[contains(@href, '#')]")
                        if error_links:
                            logger.info(f"[UniversalApplier] Self-Healing: Found {len(error_links)} flagged questions. Resolving...")
                            for err_link in error_links:
                                href = err_link.get_attribute("href") or ""
                                if "#" in href:
                                    target_id = href.split("#")[-1]
                                    target_field = self.driver.find_elements(By.ID, target_id)
                                    if target_field:
                                        tf = target_field[0]
                                        # Look for radio buttons or selects in container
                                        container = tf.find_element(By.XPATH, "ancestor::div[contains(@class, 'Container') or contains(@class, 'Field') or contains(@class, 'question')]")
                                        radios = container.find_elements(By.XPATH, ".//input[@type='radio'] | .//div[@role='radio'] | .//button")
                                        for r in radios:
                                            r_txt = r.text.lower()
                                            if "no" in r_txt:
                                                InvisibleDotsStealth.human_move_and_click(self.driver, r)
                                                logger.info("Self-healed missing radio with 'No'.")
                                                break
                            # Re-click Submit after healing
                            time.sleep(1.0)
                            InvisibleDotsStealth.human_move_and_click(self.driver, btn)
                            time.sleep(7.0)
                            page_text_healed = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                            if any(marker in page_text_healed for marker in success_markers):
                                logger.info(f"[UniversalApplier] ✅ VERIFIED TERMINAL SUCCESS (After Self-Healing) for '{company}'!")
                                return True

                        logger.warning(f"[UniversalApplier] Submit clicked but terminal state unconfirmed. URL: {after_url}")
                        return False
                except Exception:
                    continue

        logger.warning(f"[UniversalApplier] No clickable submit button found for '{company}'.")
        return False

    def _get_label_for_element(self, element) -> str:
        try:
            parent = element.find_element(By.XPATH, "ancestor::div[contains(@class, 'field') or contains(@class, 'form-group') or contains(@class, 'select__container') or contains(@class, 'ashby')]")
            labels = parent.find_elements(By.TAG_NAME, "label")
            if labels and labels[0].text.strip():
                return labels[0].text.strip()
        except Exception:
            pass
        return element.get_attribute("aria-label") or element.get_attribute("placeholder") or element.get_attribute("name") or element.get_attribute("id") or ""
