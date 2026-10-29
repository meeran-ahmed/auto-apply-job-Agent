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
            time.sleep(2)

            pi = self.profile_data.get("personal_information", {})
            first_name = str(pi.get("name", "Meeran")).strip()
            last_name = str(pi.get("surname", "Ahmed R.")).strip()
            full_name = f"{first_name} {last_name}".strip()
            email = str(pi.get("email", "meeranahmed17@gmail.com")).strip()
            phone = str(pi.get("phone", "+91 8015186448")).strip()
            city = str(pi.get("city", "Chennai")).strip()
            portfolio = "https://meeran-portfolio.antideploy.app"
            github = str(pi.get("github", "https://github.com/meeranahmed")).strip()
            linkedin = str(pi.get("linkedin", "https://www.linkedin.com/in/meeran-ahmed-r/")).strip()

            # 2. Fill standard personal fields
            self._fill_field(["first_name", "first-name", "fname"], first_name)
            self._fill_field(["last_name", "last-name", "lname"], last_name)
            self._fill_field(["name", "full_name", "full-name"], full_name)
            self._fill_field(["email"], email)
            self._fill_field(["phone", "cell", "mobile"], phone)

            # Country dropdown
            self._fill_react_select("country", "India")

            # Candidate Location (React Select or text)
            try:
                loc_inputs = self.driver.find_elements(By.ID, "candidate-location")
                for loc_input in loc_inputs:
                    loc_input.send_keys("Chennai, India")
                    time.sleep(1)
                    loc_input.send_keys(Keys.ARROW_DOWN)
                    loc_input.send_keys(Keys.ENTER)
                    loc_input.send_keys(Keys.ESCAPE)
                    logger.info("Set candidate-location: Chennai, India")
            except Exception as e:
                logger.debug(f"candidate-location error: {e}")

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

            # 4. Fill Links (LinkedIn, Portfolio, GitHub) and text inputs by Label
            labels = self.driver.find_elements(By.TAG_NAME, "label")
            for label_el in labels:
                try:
                    for_id = label_el.get_attribute("for")
                    lt = label_el.text.strip().lower()
                    if not for_id or not lt:
                        continue

                    # Check if matching input exists
                    target_inputs = self.driver.find_elements(By.ID, for_id)
                    if not target_inputs:
                        continue
                    inp = target_inputs[0]

                    # Skip file, submit, hidden inputs
                    inp_type = (inp.get_attribute("type") or "text").lower()
                    if inp_type in ["file", "submit", "hidden", "button"]:
                        continue

                    val = (inp.get_attribute("value") or "").strip()

                    # React-Select combobox
                    role = inp.get_attribute("role") or ""
                    classes = inp.get_attribute("class") or ""
                    if role == "combobox" or "select__input" in classes or "select-shell" in classes:
                        self._handle_react_select(inp, lt)
                        continue

                    # Standard text/url inputs
                    if not val and inp_type in ["text", "url", "tel"]:
                        if "linkedin" in lt:
                            inp.send_keys(linkedin)
                        elif any(k in lt for k in ["portfolio", "website", "personal link", "personal website", "project"]):
                            inp.send_keys(portfolio)
                        elif "github" in lt:
                            inp.send_keys(github)
                        elif any(k in lt for k in ["prefer us to use", "preferred name", "nickname"]):
                            inp.send_keys(first_name)
                        elif "gitlab username" in lt:
                            inp.send_keys("meeranahmed")
                        elif any(k in lt for k in ["skills", "technologies", "languages"]):
                            inp.send_keys("Python, React, Node.js, TypeScript, PostgreSQL, Implementation Engineering")
                        else:
                            # Contextual answer
                            ans = self._generate_answer(lt, job_title)
                            inp.send_keys(ans)
                        time.sleep(0.3)
                except Exception:
                    continue

            # 5. Handle standard HTML selects (if any legacy boards)
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
                        if "country" in label and "india" in ot:
                            select.select_by_visible_text(opt.text)
                            matched = True
                            break
                        if any(w in label for w in ["authorized", "legally", "eligible"]):
                            if "yes" in ot or "authorized" in ot:
                                select.select_by_visible_text(opt.text)
                                matched = True
                                break
                        elif any(w in label for w in ["sponsorship", "require", "sponsor"]):
                            if "no" in ot:
                                select.select_by_visible_text(opt.text)
                                matched = True
                                break
                        elif "gender" in label:
                            if "male" in ot:
                                select.select_by_visible_text(opt.text)
                                matched = True
                                break
                        elif any(w in label for w in ["hispanic", "latino"]):
                            if "no" in ot:
                                select.select_by_visible_text(opt.text)
                                matched = True
                                break
                        elif "veteran" in label:
                            if "not" in ot:
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

            # 6. Handle custom textareas
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

            # 7. Check all compliance, consent, and agreement checkboxes
            checkboxes = self.driver.find_elements(By.XPATH, "//input[@type='checkbox']")
            for cb in checkboxes:
                try:
                    if not cb.is_selected():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cb)
                        time.sleep(0.2)
                        self.driver.execute_script("arguments[0].click();", cb)
                        logger.info("Checked compliance / terms checkbox.")
                except Exception:
                    pass

            # 8. Submit Application
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)

            submit_elements = self.driver.find_elements(
                By.XPATH,
                "//button[contains(translate(., 'SUBMITAPPLY', 'submitapply'), 'submit') or contains(translate(., 'SUBMITAPPLY', 'submitapply'), 'apply') or contains(translate(., 'SEND', 'send'), 'send')] | "
                "//input[@type='submit'] | "
                "//input[contains(@value, 'Submit') or contains(@value, 'Apply')] | "
                "//button[@type='submit'] | "
                "//button[contains(@id, 'submit') or contains(@class, 'submit')]"
            )
            for btn in submit_elements:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(1)
                        self.driver.execute_script("arguments[0].click();", btn)
                        logger.info("Clicked Greenhouse Submit button!")
                        time.sleep(7)

                        # Strict Submission Verification
                        after_url = self.driver.current_url.lower()
                        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                        success_keywords = [
                            "thank you for applying", "application submitted", 
                            "received your application", "application has been received", 
                            "thank you for your interest", "we have received your application"
                        ]

                        if any(kw in page_text for kw in success_keywords) or any(p in after_url for p in ["/confirmation", "/thanks", "/applied", "/success"]):
                            logger.info("[Greenhouse] VERIFIED SUCCESS: Application confirmation received!")
                            return True

                        logger.warning(f"[Greenhouse] Form did not transition to confirmation page. Current URL: {after_url}")
                        return False
                except Exception:
                    continue

            logger.warning("No clickable Greenhouse submit button found.")
            return False

        except Exception as e:
            logger.error(f"Error applying on Greenhouse: {e}")
            return False

    def _handle_react_select(self, element, label: str):
        try:
            val = ""
            if "country" in label or "residence" in label or "located" in label:
                val = "India"
            elif any(w in label for w in ["language", "speak"]):
                val = "English"
            elif any(w in label for w in ["gender", "identify"]):
                val = "Male"
            elif any(w in label for w in ["hispanic", "latino"]):
                val = "No"
            elif "veteran" in label:
                val = "I am not a protected veteran"
            elif any(w in label for w in ["disability", "physical"]):
                val = "No"
            elif any(w in label for w in ["authorized", "eligible", "authorization", "evidence"]):
                val = "Yes"
            elif any(w in label for w in ["sponsorship", "require", "sponsor"]):
                val = "No"
            elif any(w in label for w in ["pronoun"]):
                val = "He/Him"
            elif any(w in label for w in ["how did you hear", "source"]):
                val = "LinkedIn"
            elif any(w in label for w in ["previously worked", "employed by", "restrictions", "agreement"]):
                val = "No"
            elif any(w in label for w in ["read", "policy", "terms", "agree", "consent", "privacy"]):
                val = "Yes"
            else:
                val = "Yes"

            if val:
                element.send_keys(val)
                time.sleep(0.5)
                element.send_keys(Keys.ENTER)
                element.send_keys(Keys.ESCAPE)
                logger.info(f"Set React-Select for '{label[:30]}' to '{val}'")
        except Exception as e:
            logger.debug(f"React select error: {e}")

    def _fill_react_select(self, field_id: str, value: str):
        try:
            els = self.driver.find_elements(By.ID, field_id)
            for el in els:
                el.send_keys(value)
                time.sleep(0.5)
                el.send_keys(Keys.ENTER)
                el.send_keys(Keys.ESCAPE)
                logger.info(f"Dropdown '{field_id}' set to: {value}")
        except Exception as e:
            logger.debug(f"Dropdown '{field_id}' note: {e}")

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
        if any(w in q for w in ["notice", "availability", "when can you start", "start date"]):
            return "Immediate (0 days notice, ready to join right away)."
        if any(w in q for w in ["salary", "compensation", "expectation", "ctc"]):
            return "Negotiable based on company standards and role responsibilities."
        if any(w in q for w in ["location", "relocate", "hybrid", "remote", "chennai", "bangalore"]):
            return "Fully available for remote work as well as hybrid setups in Chennai or Bangalore."
        if any(w in q for w in ["implementation", "deploy", "onboarding", "fde", "forward"]):
            return (
                "As an Implementation Executive at Pathfinder Enterprises Solutions, I led end-to-end "
                "deployment of AI-based retail software solutions, customer onboarding, payment gateway "
                "integrations, and cross-functional technical troubleshooting, ensuring fast time-to-value."
            )
        if any(w in q for w in ["ai", "vibe", "claude", "cursor", "llm", "tools"]):
            return (
                "I actively leverage AI-augmented development workflows (Claude Code, Cursor, LLMs) to build "
                "and deploy production-ready full-stack applications with high speed, clean architecture, and strict testing."
            )
        if any(w in q for w in ["why", "interest", "reason", "cover letter", "about you"]):
            return (
                f"I am deeply excited to apply for the {job_title} role. With hands-on experience in full-stack development "
                "(React, Node.js, TypeScript, PostgreSQL) and software implementation, I have built production platforms like "
                "Kamyaab Academy (1,000+ users) and Vexa AI. I look forward to contributing impactful, scalable solutions."
            )
        if any(w in q for w in ["project", "achievement", "proud"]):
            return (
                "One of my most notable achievements was architecting Kamyaab Academy, an educational platform "
                "supporting 1,000+ active users. I implemented a robust 3-tier architecture with PostgreSQL, "
                "Google OAuth 2.0, and payment gateway integrations, achieving sub-second API latencies."
            )
        return "Yes, fully experienced and aligned with the role requirements."
