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
            # Auto-normalize direct application URLs for Ashby and Lever
            clean_url = target_url.strip()
            if "ashbyhq.com" in clean_url and not clean_url.endswith("/application"):
                clean_url = clean_url.rstrip("/") + "/application"
            elif "lever.co" in clean_url and not clean_url.endswith("/apply"):
                clean_url = clean_url.rstrip("/") + "/apply"

            self.driver.get(clean_url)
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
        """Fills First Name, Last Name, Full Name, Email, Phone, LinkedIn, and Portfolio."""
        field_mappings = [
            (["first_name", "first-name", "fname", "given-name"], self.first_name),
            (["last_name", "last-name", "lname", "family-name"], self.last_name),
            (["name", "full_name", "full-name", "_systemfield_name"], self.full_name),
            (["email", "_systemfield_email"], self.email),
            (["phone", "cell", "mobile", "tel", "_systemfield_phone"], self.phone),
            (["linkedin", "linkedin_profile", "linkedin-profile", "linkedin_url", "linkedinurl"], self.linkedin),
            (["github", "github_profile", "github-profile", "github_url"], self.github),
            (["portfolio", "website", "portfolio_url", "portfoliourl"], self.portfolio),
            (["candidate-location", "city", "location"], "Chennai, India")
        ]

        for keys, val in field_mappings:
            for k in keys:
                selectors = [
                    f"input#{k}", f"input[name='{k}']", f"input[id='{k}']",
                    f"input[placeholder*='{k}']"
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
        """Locates and uploads resume PDF, then waits for React DOM re-render."""
        if not self.resume_path:
            return
        try:
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            for fi in file_inputs:
                try:
                    fi.send_keys(self.resume_path)
                    logger.info(f"Uploaded resume file: {self.resume_path}")
                    # Allow Ashby / Greenhouse React to finish autofilling & re-rendering DOM
                    time.sleep(5.5)
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
        """Leverages Gemini Neural Synthesizer for text inputs, textareas, and toggle buttons."""
        # 1. Handle all text inputs, url inputs, and textareas
        inputs = self.driver.find_elements(By.XPATH, "//input[@type='text' or @type='email' or @type='tel' or @type='url' or not(@type)] | //textarea")
        for inp in inputs:
            try:
                if not inp.is_displayed():
                    continue

                # Skip recaptcha tokens and hidden tokens
                el_id_raw = (inp.get_attribute("id") or "").lower()
                el_name_raw = (inp.get_attribute("name") or "").lower()
                if "recaptcha" in el_id_raw or "recaptcha" in el_name_raw or "csrf" in el_name_raw:
                    continue

                lbl = self._get_label_for_element(inp)
                lbl_lower = lbl.lower()
                name_attr = el_name_raw
                id_attr = el_id_raw
                combined = f"{lbl_lower} {name_attr} {id_attr}"

                is_textarea = inp.tag_name.lower() == "textarea"
                is_name_field = (
                    not is_textarea and (
                        any(k in lbl_lower for k in ["full name", "your name", "first name", "last name", "candidate name", "legal name"]) or
                        lbl_lower.strip() in ["name", "name *", "name*"] or
                        name_attr in ["name", "full_name", "fullname", "candidate_name", "_systemfield_name"] or
                        id_attr in ["name", "full_name", "fullname", "_systemfield_name"]
                    )
                ) and "company" not in combined and "user" not in combined

                if "email" in combined or name_attr in ["email", "_systemfield_email"] or id_attr in ["email", "_systemfield_email"]:
                    curr = (inp.get_attribute("value") or "").strip()
                    if not curr or "@" not in curr:
                        inp.clear()
                        InvisibleDotsStealth.human_type(self.driver, inp, self.email)
                        logger.info("Filled Email: " + self.email)
                elif any(p in combined for p in ["phone", "mobile", "cell", "tel"]):
                    curr = (inp.get_attribute("value") or "").strip()
                    if not curr:
                        inp.clear()
                        InvisibleDotsStealth.human_type(self.driver, inp, self.phone)
                        logger.info("Filled Phone: " + self.phone)
                elif is_name_field:
                    curr = (inp.get_attribute("value") or "").strip()
                    if not curr:
                        inp.clear()
                        InvisibleDotsStealth.human_type(self.driver, inp, self.full_name)
                        logger.info("Filled Name: " + self.full_name)
                elif "linkedin" in combined:
                    curr = (inp.get_attribute("value") or "").strip()
                    if not curr:
                        inp.clear()
                        InvisibleDotsStealth.human_type(self.driver, inp, self.linkedin)
                        logger.info("Filled LinkedIn")
                elif "github" in combined:
                    curr = (inp.get_attribute("value") or "").strip()
                    if not curr:
                        inp.clear()
                        InvisibleDotsStealth.human_type(self.driver, inp, self.github)
                        logger.info("Filled GitHub")
                elif any(w in combined for w in ["portfolio", "website", "personal link", "project url"]):
                    curr = (inp.get_attribute("value") or "").strip()
                    if not curr:
                        inp.clear()
                        InvisibleDotsStealth.human_type(self.driver, inp, self.portfolio)
                        logger.info("Filled Portfolio")
                elif any(w in combined for w in ["country", "location", "located in", "current location", "residence"]):
                    curr = (inp.get_attribute("value") or "").strip()
                    if not curr:
                        inp.clear()
                        InvisibleDotsStealth.human_type(self.driver, inp, "India")
                        time.sleep(0.8)
                        try:
                            from selenium.webdriver.common.keys import Keys
                            opts = self.driver.find_elements(By.XPATH, "//*[@role='option']")
                            if opts:
                                InvisibleDotsStealth.human_move_and_click(self.driver, opts[0])
                            else:
                                inp.send_keys(Keys.ENTER)
                        except Exception:
                            pass
                        logger.info("Filled Country/Location: India")
                elif "notice" in combined or "start" in combined:
                    curr = (inp.get_attribute("value") or "").strip()
                    if not curr:
                        inp.clear()
                        InvisibleDotsStealth.human_type(self.driver, inp, "Immediate (0 days)")
                elif "salary" in combined or "compensation" in combined or "ctc" in combined:
                    curr = (inp.get_attribute("value") or "").strip()
                    if not curr:
                        inp.clear()
                        InvisibleDotsStealth.human_type(self.driver, inp, "Competitive")
                else:
                    curr = (inp.get_attribute("value") or "").strip()
                    if not curr and lbl:
                        answer = self.synthesizer.synthesize_answer(lbl, job_title, company)
                        InvisibleDotsStealth.human_type(self.driver, inp, answer)
                        logger.info(f"Synthesized recruiter answer for [{lbl[:30]}]: {answer[:50]}...")
            except Exception:
                pass

        # 2. Handle all button toggles (Yes / No) across question containers
        containers = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'fieldEntry') or contains(@class, 'ashby-application-form-field-entry')]")
        for c in containers:
            try:
                yes_no_btns = c.find_elements(By.XPATH, ".//button[text()='Yes' or text()='No']")
                if len(yes_no_btns) >= 2:
                    c_text = c.text.lower()
                    already_selected = any("active" in (b.get_attribute("class") or "").lower() or b.get_attribute("aria-pressed") == "true" for b in yes_no_btns)
                    if not already_selected:
                        target_val = "no" if ("sponsor" in c_text or "visa" in c_text) else "yes"
                        for b in yes_no_btns:
                            if b.text.strip().lower() == target_val:
                                InvisibleDotsStealth.human_move_and_click(self.driver, b)
                                logger.info(f"Clicked '{b.text.strip()}' for: {c_text[:35]}...")
                                break
            except Exception:
                pass

        # Handle Ashby and general radio groups (EEO, Veteran, Disability, Sponsorship, Authorization)
        fieldsets = self.driver.find_elements(By.XPATH, "//fieldset | //div[contains(@class, 'radio-group')] | //div[contains(@class, 'RadioGroup')]")
        for fs in fieldsets:
            try:
                fs_text = fs.text.lower()
                labels = fs.find_elements(By.TAG_NAME, "label")
                if not labels:
                    continue

                # 1. Veteran Status
                if "veteran" in fs_text:
                    for lbl in labels:
                        lt = lbl.text.lower()
                        if "not a protected veteran" in lt or "decline" in lt:
                            InvisibleDotsStealth.human_move_and_click(self.driver, lbl)
                            logger.info(f"Selected Veteran radio: {lbl.text.strip()}")
                            break

                # 2. Disability Status
                elif "disability" in fs_text or "handicap" in fs_text:
                    for lbl in labels:
                        lt = lbl.text.lower()
                        if "don't have" in lt or "do not have" in lt or "no" in lt or "decline" in lt:
                            InvisibleDotsStealth.human_move_and_click(self.driver, lbl)
                            logger.info(f"Selected Disability radio: {lbl.text.strip()}")
                            break

                # 3. Gender
                elif "gender" in fs_text:
                    for lbl in labels:
                        lt = lbl.text.lower()
                        if "male" in lt or "man" in lt:
                            InvisibleDotsStealth.human_move_and_click(self.driver, lbl)
                            logger.info(f"Selected Gender radio: {lbl.text.strip()}")
                            break

                # 4. Hispanic / Latino
                elif "hispanic" in fs_text or "latino" in fs_text:
                    for lbl in labels:
                        lt = lbl.text.lower()
                        if lt == "no" or "not hispanic" in lt or "no," in lt:
                            InvisibleDotsStealth.human_move_and_click(self.driver, lbl)
                            logger.info(f"Selected Hispanic/Latino radio: {lbl.text.strip()}")
                            break

                # 5. Race / Ethnicity
                elif "race" in fs_text or "ethnicity" in fs_text:
                    for lbl in labels:
                        lt = lbl.text.lower()
                        if "asian" in lt or "decline" in lt:
                            InvisibleDotsStealth.human_move_and_click(self.driver, lbl)
                            logger.info(f"Selected Race radio: {lbl.text.strip()}")
                            break

                # 6. Sponsorship
                elif "sponsor" in fs_text or "visa" in fs_text:
                    for lbl in labels:
                        lt = lbl.text.lower()
                        if lt == "no" or "no," in lt or "do not" in lt:
                            InvisibleDotsStealth.human_move_and_click(self.driver, lbl)
                            logger.info(f"Selected Sponsorship radio: {lbl.text.strip()}")
                            break

                # 7. Work Authorization / 18+
                elif "authorized" in fs_text or "eligible" in fs_text or "18" in fs_text:
                    for lbl in labels:
                        lt = lbl.text.lower()
                        if lt == "yes" or "yes," in lt:
                            InvisibleDotsStealth.human_move_and_click(self.driver, lbl)
                            logger.info(f"Selected Authorization radio: {lbl.text.strip()}")
                            break

                # 8. Source / How did you hear
                elif any(w in fs_text for w in ["hear about", "source", "how did you hear"]):
                    for lbl in labels:
                        lt = lbl.text.lower()
                        if any(w in lt for w in ["job board", "linkedin", "social media", "internet", "website", "other"]):
                            InvisibleDotsStealth.human_move_and_click(self.driver, lbl)
                            logger.info(f"Selected Source radio: {lbl.text.strip()}")
                            break

                # 9. General Custom Question Radio Fallback
                else:
                    is_checked = any(r.is_selected() or "checked" in (r.get_attribute("class") or "").lower() or r.get_attribute("aria-checked") == "true" for r in fs.find_elements(By.XPATH, ".//input[@type='radio'] | .//div[@role='radio']"))
                    if not is_checked:
                        chosen = None
                        if "clearance" in fs_text:
                            for lbl in labels:
                                lt = lbl.text.lower()
                                if "do not have" in lt or "none" in lt or "no" in lt:
                                    chosen = lbl
                                    break
                        elif any(k in fs_text for k in ["relocat", "based in", "located in", "ottawa", "london", "travel"]):
                            for lbl in labels:
                                lt = lbl.text.lower()
                                if "open to relocation" in lt or "open to travel" in lt or "yes" in lt:
                                    chosen = lbl
                                    break
                        elif any(k in fs_text for k in ["hours", "schedule", "timezone", "time zone", "comfortable"]):
                            for lbl in labels:
                                lt = lbl.text.lower()
                                if "yes" in lt or "comfortable" in lt or "agree" in lt:
                                    chosen = lbl
                                    break
                        else:
                            for lbl in labels:
                                if "yes" in lbl.text.lower():
                                    chosen = lbl
                                    break
                        if not chosen and labels:
                            chosen = labels[0]
                        if chosen:
                            InvisibleDotsStealth.human_move_and_click(self.driver, chosen)
                            logger.info(f"Selected general radio option for [{fs_text[:30]}]: {chosen.text.strip()}")
            except Exception:
                pass

        # Also handle any standard isolated radio inputs
        for radio in self.driver.find_elements(By.XPATH, "//input[@type='radio'] | //div[@role='radio']"):
            try:
                label_text = self._get_label_for_element(radio).lower()
                r_val = (radio.get_attribute("value") or radio.text or "").lower()
                if "sponsor" in label_text and "no" in r_val:
                    InvisibleDotsStealth.human_move_and_click(self.driver, radio)
                elif ("authorized" in label_text or "eligible" in label_text) and "yes" in r_val:
                    InvisibleDotsStealth.human_move_and_click(self.driver, radio)
            except Exception:
                pass

    def _check_compliance_boxes(self):
        """Auto-checks mandatory compliance, GDPR, and data policy checkboxes."""
        # 1. Check HTML input checkboxes
        checkboxes = self.driver.find_elements(By.XPATH, "//input[@type='checkbox']")
        for cb in checkboxes:
            try:
                if not cb.is_selected():
                    # Click parent label or checkbox itself
                    try:
                        parent = cb.find_element(By.XPATH, "./..")
                        InvisibleDotsStealth.human_move_and_click(self.driver, parent)
                    except Exception:
                        InvisibleDotsStealth.human_move_and_click(self.driver, cb)
                    logger.info("Checked compliance checkbox.")
            except Exception:
                pass

        # 2. Check Ashby custom checkbox labels (e.g. 'I agree')
        agree_labels = self.driver.find_elements(By.XPATH, "//label[contains(translate(., 'AGREE', 'agree'), 'agree') or contains(translate(., 'CONSENT', 'consent'), 'consent')]")
        for al in agree_labels:
            try:
                InvisibleDotsStealth.human_move_and_click(self.driver, al)
                logger.info(f"Checked consent label: {al.text.strip()[:30]}")
            except Exception:
                pass

    def _execute_submit_and_verify(self, job_title: str, company: str) -> bool:
        """Finds submit button, executes Bézier click, and verifies terminal confirmation."""
        submit_selectors = [
            "//button[contains(@class, 'submit') or @type='submit']",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
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

                        # Poll for up to 30 seconds for network mutation & transition to finish
                        for _ in range(15):
                            time.sleep(2.0)
                            after_url = self.driver.current_url.lower()
                            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()

                            if any(marker in page_text for marker in success_markers) or any(p in after_url for p in ["/confirmation", "/thanks", "/applied", "/success"]):
                                shot_post = f"data_folder/output/submissions/post_{company.lower().replace(' ', '_')}_{int(time.time())}.png"
                                self.driver.save_screenshot(shot_post)
                                logger.info(f"[UniversalApplier] ✅ VERIFIED TERMINAL SUCCESS: Application confirmed for '{company}'!")
                                return True

                        # Check for 90-day application cooldown
                        if "within the last 90 days" in page_text or "limiting applications" in page_text or "already applied" in page_text:
                            logger.warning(f"[UniversalApplier] Candidate has already applied to {company} within recent window: {page_text[:100]}...")
                            return False

                        shot_post = f"data_folder/output/submissions/post_{company.lower().replace(' ', '_')}_{int(time.time())}.png"
                        self.driver.save_screenshot(shot_post)
                        after_url = self.driver.current_url.lower()

                        # Self-Healing: Check if Ashby or Lever flagged missing required fields
                        error_links = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'Error') or contains(@class, 'warning')]//a[contains(@href, '#')]")
                        if error_links:
                            logger.info(f"[UniversalApplier] Self-Healing: Found {len(error_links)} flagged questions. Resolving...")
                            for err_link in error_links:
                                err_text = err_link.text.lower()
                                href = err_link.get_attribute("href") or ""
                                if "#" in href:
                                    target_id = href.split("#")[-1]
                                    target_field = self.driver.find_elements(By.ID, target_id)
                                    if target_field:
                                        tf = target_field[0]
                                        tag = tf.tag_name.lower()
                                        tf_type = (tf.get_attribute("type") or "").lower()
                                        
                                        # If it's a URL or text input or textarea
                                        if tag in ["input", "textarea"]:
                                            if "linkedin" in err_text or "linkedin" in target_id.lower():
                                                tf.clear()
                                                InvisibleDotsStealth.human_type(self.driver, tf, self.linkedin)
                                                logger.info("Self-healed missing field: LinkedIn URL")
                                            elif "github" in err_text or "github" in target_id.lower():
                                                tf.clear()
                                                InvisibleDotsStealth.human_type(self.driver, tf, self.github)
                                                logger.info("Self-healed missing field: GitHub URL")
                                            elif any(p in err_text for p in ["portfolio", "website"]):
                                                tf.clear()
                                                InvisibleDotsStealth.human_type(self.driver, tf, self.portfolio)
                                                logger.info("Self-healed missing field: Portfolio URL")
                                            elif any(loc in err_text for loc in ["location", "city", "country", "where are you"]):
                                                tf.clear()
                                                InvisibleDotsStealth.human_type(self.driver, tf, "Chennai, India")
                                                logger.info("Self-healed missing field: Location")
                                            elif tf_type in ["text", "url", ""] or tag == "textarea":
                                                synth_ans = self.synthesizer.synthesize_answer(err_link.text, job_title, company)
                                                tf.clear()
                                                InvisibleDotsStealth.human_type(self.driver, tf, synth_ans)
                                                logger.info(f"Self-healed text field [{err_link.text}]: {synth_ans[:40]}...")
                                        
                                        # Look for radio buttons, checkboxes, or buttons in container or fieldset
                                        containers = tf.find_elements(By.XPATH, "ancestor::div[contains(@class, 'Container') or contains(@class, 'Field') or contains(@class, 'question') or contains(@class, 'fieldEntry')] | ancestor::fieldset")
                                        if containers:
                                            container = containers[0]
                                            c_lower = container.text.lower()
                                            buttons_and_radios = container.find_elements(By.XPATH, ".//button | .//input[@type='radio'] | .//div[@role='radio'] | .//label")
                                            target_choice = "no" if ("sponsor" in c_lower or "visa" in c_lower) else "yes"
                                            
                                            clicked = False
                                            if "clearance" in c_lower:
                                                for r in buttons_and_radios:
                                                    if "do not have" in r.text.lower() or "none" in r.text.lower():
                                                        InvisibleDotsStealth.human_move_and_click(self.driver, r)
                                                        clicked = True
                                                        break
                                            elif "relocat" in c_lower or "based in" in c_lower:
                                                for r in buttons_and_radios:
                                                    if "open to relocation" in r.text.lower() or "open to travel" in r.text.lower():
                                                        InvisibleDotsStealth.human_move_and_click(self.driver, r)
                                                        clicked = True
                                                        break
                                            elif "hear about" in c_lower or "source" in c_lower:
                                                for r in buttons_and_radios:
                                                    if any(w in r.text.lower() for w in ["job board", "linkedin", "social media", "internet", "website", "other"]):
                                                        InvisibleDotsStealth.human_move_and_click(self.driver, r)
                                                        clicked = True
                                                        break
                                            
                                            if not clicked:
                                                for r in buttons_and_radios:
                                                    r_txt = r.text.strip().lower()
                                                    if r_txt == target_choice or (target_choice == "yes" and ("yes" in r_txt or "comfortable" in r_txt or "agree" in r_txt)):
                                                        InvisibleDotsStealth.human_move_and_click(self.driver, r)
                                                        clicked = True
                                                        break
                                            
                                            if not clicked and buttons_and_radios:
                                                InvisibleDotsStealth.human_move_and_click(self.driver, buttons_and_radios[0])
                                                clicked = True
                                                
                                            if clicked:
                                                logger.info("Self-healed container choice successfully.")
                            # Re-click Submit after healing
                            time.sleep(1.5)
                            InvisibleDotsStealth.human_move_and_click(self.driver, btn)
                            time.sleep(7.0)
                            page_text_healed = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                            if any(marker in page_text_healed for marker in success_markers) or any(p in self.driver.current_url.lower() for p in ["/confirmation", "/thanks", "/applied", "/success"]):
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
            el_id = element.get_attribute("id")
            if el_id:
                lbls = self.driver.find_elements(By.XPATH, f"//label[@for='{el_id}']")
                if lbls and lbls[0].text.strip():
                    return lbls[0].text.strip()

            containers = element.find_elements(By.XPATH, "ancestor::div[contains(@class, 'fieldEntry') or contains(@class, 'ashby-application-form-field-entry') or contains(@class, 'form-group') or contains(@class, 'field-container') or contains(@class, 'form-field')]")
            if containers:
                c = containers[0]
                lbls = c.find_elements(By.TAG_NAME, "label")
                if lbls and lbls[0].text.strip():
                    return lbls[0].text.strip()
                headings = c.find_elements(By.XPATH, ".//h1|.//h2|.//h3|.//h4|.//h5|.//legend|.//span[contains(@class, 'label')]")
                if headings and headings[0].text.strip():
                    return headings[0].text.strip()
                lines = [l.strip() for l in c.text.split('\n') if l.strip()]
                if lines:
                    return lines[0]
        except Exception:
            pass
        return element.get_attribute("aria-label") or element.get_attribute("placeholder") or element.get_attribute("name") or element.get_attribute("id") or ""
