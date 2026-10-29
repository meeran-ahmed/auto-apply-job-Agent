import json
import os
import random
import re
import time
import urllib.parse
from itertools import product
from pathlib import Path

from inputimeout import inputimeout, TimeoutOccurred
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

import src.utils as utils
import yaml
from app_config import MINIMUM_WAIT_TIME
from src.job import Job
from src.aihawk_easy_applier import AIHawkEasyApplier
from src.ats.ats_manager import ATSManager
from loguru import logger


class EnvironmentKeys:
    def __init__(self):
        logger.debug("Initializing EnvironmentKeys")
        self.skip_apply = self._read_env_key_bool("SKIP_APPLY")
        self.disable_description_filter = self._read_env_key_bool("DISABLE_DESCRIPTION_FILTER")
        logger.debug(f"EnvironmentKeys initialized: skip_apply={self.skip_apply}, disable_description_filter={self.disable_description_filter}")

    @staticmethod
    def _read_env_key(key: str) -> str:
        value = os.getenv(key, "")
        logger.debug(f"Read environment key {key}: {value}")
        return value

    @staticmethod
    def _read_env_key_bool(key: str) -> bool:
        value = os.getenv(key) == "True"
        logger.debug(f"Read environment key {key} as bool: {value}")
        return value


class AIHawkJobManager:
    def __init__(self, driver):
        logger.debug("Initializing AIHawkJobManager")
        self.driver = driver
        self.set_old_answers = set()
        self.easy_applier_component = None
        logger.debug("AIHawkJobManager initialized successfully")

    def set_parameters(self, parameters=None, **kwargs):
        logger.debug("Setting parameters for AIHawkJobManager")
        if parameters is None:
            parameters = {}
        if isinstance(parameters, dict):
            parameters = {**parameters, **kwargs}
        else:
            parameters = kwargs

        self.company_blacklist = parameters.get('company_blacklist', []) or []
        self.title_blacklist = parameters.get('title_blacklist', []) or []
        self.positions = parameters.get('positions', [])
        self.locations = parameters.get('locations', [])
        self.apply_once_at_company = parameters.get('apply_once_at_company', False)
        self.base_search_url = self.get_base_search_url(parameters) if hasattr(self, 'get_base_search_url') else ""
        self.seen_jobs = []

        job_applicants_threshold = parameters.get('job_applicants_threshold', {})
        self.min_applicants = job_applicants_threshold.get('min_applicants', 0)
        self.max_applicants = job_applicants_threshold.get('max_applicants', float('inf'))

        resume_path = parameters.get('uploads', {}).get('resume', None) or parameters.get('resume_dir', None)
        self.resume_path = Path(resume_path) if resume_path else None
        out_dir = parameters.get('outputFileDirectory', parameters.get('output_file_directory', 'output'))
        self.output_file_directory = Path(out_dir) if out_dir else None
        try:
            self.env_config = EnvironmentKeys()
        except Exception:
            self.env_config = None
        logger.debug("Parameters set successfully")

    def set_gpt_answerer(self, gpt_answerer):
        logger.debug("Setting GPT answerer")
        self.gpt_answerer = gpt_answerer

    def set_resume_generator_manager(self, resume_generator_manager):
        logger.debug("Setting resume generator manager")
        self.resume_generator_manager = resume_generator_manager

    def start_applying(self):
        logger.debug("Starting job application process")
        self.easy_applier_component = AIHawkEasyApplier(self.driver, self.resume_path, self.set_old_answers,
                                                          self.gpt_answerer, self.resume_generator_manager)
        profile_data = {}
        try:
            with open("data_folder/plain_text_resume.yaml", "r", encoding="utf-8") as yf:
                profile_data = yaml.safe_load(yf) or {}
        except Exception:
            pass
        self.ats_manager = ATSManager(self.driver, str(self.resume_path or "data_folder/resume.pdf"), profile_data, self.gpt_answerer)
        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)
        page_sleep = 0
        minimum_time = MINIMUM_WAIT_TIME
        minimum_page_time = time.time() + minimum_time

        for position, location in searches:
            pos_clean = str(position).strip()
            loc_clean = str(location).strip()
            if loc_clean.lower() in ("remote", "any", "all", "worldwide") or not loc_clean:
                location_url = ""
            else:
                location_url = "&location=" + urllib.parse.quote_plus(loc_clean)

            job_page_number = -1
            logger.info(f"Starting job search for '{pos_clean}' with location '{loc_clean or 'Worldwide'}'.")

            try:
                while True:
                    page_sleep += 1
                    job_page_number += 1
                    logger.debug(f"Going to job page {job_page_number}")
                    self.next_job_page(pos_clean, location_url, job_page_number)
                    time.sleep(random.uniform(2.5, 4.5))

                    try:
                        jobs = self.get_jobs_from_page()
                        if not jobs:
                            logger.info("No more matching jobs found on this page or search completed.")
                            break
                    except Exception as e:
                        logger.error(f"Failed to retrieve jobs: {e}")
                        break

                    try:
                        self.apply_jobs(jobs)
                    except Exception as e:
                        logger.error(f"Error during job application batch: {e}")
                        continue

                    logger.debug("Applying to jobs on this page has been completed!")
                    time.sleep(random.uniform(3.0, 5.0))
                    minimum_page_time = time.time() + minimum_time
                    page_sleep += 1
            except Exception as e:
                logger.error(f"Unexpected error during job search: {e}")
                continue

            time.sleep(random.uniform(4.0, 7.0))
            minimum_page_time = time.time() + minimum_time
            page_sleep += 1

    def get_jobs_from_page(self):
        try:
            # Wait up to 6s for search results or no-results banner
            try:
                WebDriverWait(self.driver, 6).until(
                    lambda d: d.find_elements(By.XPATH, "//button[contains(@aria-label, 'Dismiss') and contains(@aria-label, 'job')]") or
                              d.find_elements(By.CSS_SELECTOR, '.scaffold-layout__list-container, .jobs-search-results-list, .jobs-search-two-pane__no-results-banner--expand')
                )
            except Exception:
                pass

            no_jobs_element = self.driver.find_elements(By.CLASS_NAME, 'jobs-search-two-pane__no-results-banner--expand')
            if isinstance(no_jobs_element, list) and len(no_jobs_element) > 0:
                first_el = no_jobs_element[0]
                text_val = getattr(first_el, 'text', '')
                page_source = getattr(self.driver, 'page_source', '')
                if (isinstance(text_val, str) and 'No matching jobs found' in text_val) or (isinstance(page_source, str) and 'unfortunately, things aren' in str(page_source).lower()):
                    logger.debug("No matching jobs found banner visible, skipping.")
                    return []
        except NoSuchElementException:
            pass

        try:
            # 1. Check modern LinkedIn dismiss buttons (25 cards per page)
            dismiss_btns = self.driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Dismiss') and contains(@aria-label, 'job')]")
            if dismiss_btns:
                cards = []
                for btn in dismiss_btns:
                    try:
                        card = btn.find_element(By.XPATH, "ancestor::div[@role='button']")
                        cards.append(card)
                    except Exception:
                        cards.append(btn)
                if cards:
                    logger.info(f"Found {len(cards)} modern LinkedIn job cards on page.")
                    return cards

            # 2. Fallback to legacy selectors
            try:
                job_results = self.driver.find_element(By.CSS_SELECTOR, ".jobs-search-results-list, .scaffold-layout__list, .scaffold-layout__list-container")
                utils.scroll_slow(self.driver, job_results)
                utils.scroll_slow(self.driver, job_results, step=300, reverse=True)
            except Exception:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, 0);")

            job_list_elements = []
            candidate_selectors = [
                ".scaffold-layout__list-container > li",
                "li.jobs-search-results__list-item",
                "li.scaffold-layout__list-item",
                "li[data-occludable-job-id]",
                "div[data-view-name='job-card']",
                "div[data-job-id]"
            ]
            for sel in candidate_selectors:
                found = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if found:
                    valid = [el for el in found if el.text.strip()]
                    if valid:
                        job_list_elements = valid
                        break

            if not job_list_elements:
                logger.debug("No job card elements found on page.")
                return []

            logger.info(f"Found {len(job_list_elements)} job cards on current page.")
            return job_list_elements

        except NoSuchElementException:
            logger.debug("No job results found on the page.")
            return []
        except Exception as e:
            logger.error(f"Error while fetching job elements: {e}")
            return []

    def apply_jobs(self, job_list_elements=None):
        if not job_list_elements:
            job_list_elements = self.get_jobs_from_page()

        if not job_list_elements:
            logger.debug("No job elements to process on this page.")
            return

        logger.info(f"Processing {len(job_list_elements)} job applications on this page...")

        for idx, el in enumerate(job_list_elements):
            try:
                # Dismiss any open modal/dialog first
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            except Exception:
                pass

            try:
                # Scroll card into view and click it to open details in right pane
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                time.sleep(random.uniform(0.6, 1.0))
                self.driver.execute_script("arguments[0].click();", el)
                time.sleep(random.uniform(1.8, 2.8))
            except Exception as e:
                logger.debug(f"Card click {idx} failed or not needed: {e}")

            current_url = str(getattr(self.driver, 'current_url', '')) if not isinstance(getattr(self.driver, 'current_url', ''), str) else self.driver.current_url
            job_id_match = re.search(r'currentJobId=(\d+)', current_url) if isinstance(current_url, str) else None
            job_id = job_id_match.group(1) if job_id_match else ""
            job_link = f"https://www.linkedin.com/jobs/view/{job_id}/" if job_id else current_url

            info = self.extract_job_information_from_tile(el)
            job_title = info[0]
            company = info[1]
            location = info[2]
            job = Job(title=job_title, company=company, location=location, link=job_link, apply_method="Easy Apply")

            if not job.title:
                logger.debug("Empty job title, skipping.")
                continue

            if self.is_blacklisted(job.title, job.company, job.link):
                logger.info(f"Skipping blacklisted job: '{job.title}' at '{job.company}'")
                self.write_to_file(job, "skipped")
                continue

            if self.is_already_applied_to_job(job.title, job.company, job.link):
                self.write_to_file(job, "skipped")
                continue

            if self.is_already_applied_to_company(job.company):
                self.write_to_file(job, "skipped")
                continue

            try:
                # Look for Easy Apply button on the active job details pane with short wait
                clickable_easy_apply = None
                for _ in range(4):
                    easy_apply_buttons = self.driver.find_elements(
                        By.XPATH,
                        "//button[contains(., 'Easy Apply') or contains(@aria-label, 'Easy Apply to') or contains(@class, 'jobs-apply-button')]"
                    )
                    for b in easy_apply_buttons:
                        try:
                            btn_text = b.text if isinstance(getattr(b, 'text', None), str) else ""
                            aria_label = b.get_attribute("aria-label") if hasattr(b, 'get_attribute') else ""
                            label_str = aria_label if isinstance(aria_label, str) else ""
                            combo_text = (btn_text + " " + label_str).lower()
                            if b.is_displayed() and b.is_enabled() and "easy apply" in combo_text:
                                clickable_easy_apply = b
                                break
                        except Exception:
                            continue
                    if clickable_easy_apply:
                        break
                    time.sleep(0.8)

                if not clickable_easy_apply:
                    # Check for External Apply button on details pane
                    external_apply_btns = self.driver.find_elements(
                        By.XPATH,
                        "//button[contains(@class, 'jobs-apply-button') and contains(., 'Apply')] | //a[contains(@class, 'jobs-apply-button')]"
                    )
                    clickable_external = None
                    for eb in external_apply_btns:
                        try:
                            if eb.is_displayed() and eb.is_enabled():
                                clickable_external = eb
                                break
                        except Exception:
                            continue

                    if clickable_external:
                        logger.info(f"External Apply detected for '{job.title}' at '{job.company}'. Initiating ATS Form Filler...")
                        original_window = self.driver.current_window_handle
                        self.driver.execute_script("arguments[0].click();", clickable_external)
                        time.sleep(3.5)

                        # Switch to new tab if opened
                        for wh in self.driver.window_handles:
                            if wh != original_window:
                                self.driver.switch_to.window(wh)
                                break

                        try:
                            ats_success = self.ats_manager.apply_to_external_page(job.title, job.company)
                            if ats_success:
                                self.write_to_file(job, "success")
                                logger.info(f"Successfully submitted external ATS application for '{job.title}' at '{job.company}'!")
                            else:
                                self.write_to_file(job, "skipped")
                        except Exception as e:
                            logger.error(f"External ATS apply error: {e}")
                            self.write_to_file(job, "failed")
                        finally:
                            if len(self.driver.window_handles) > 1 and self.driver.current_window_handle != original_window:
                                self.driver.close()
                            self.driver.switch_to.window(original_window)
                            time.sleep(1.5)
                        continue

                    logger.debug(f"No visible Apply button for '{job.title}' at '{job.company}', skipping.")
                    self.write_to_file(job, "skipped")
                    continue

                logger.info(f"Applying to: '{job.title}' at '{job.company}' ({job.link})")
                try:
                    actions = ActionChains(self.driver)
                    actions.move_to_element(clickable_easy_apply).click().perform()
                except Exception:
                    try:
                        clickable_easy_apply.click()
                    except Exception:
                        pass
                time.sleep(0.5)

                # Pass job info to GPT Answerer
                if hasattr(self, 'gpt_answerer') and self.gpt_answerer:
                    self.gpt_answerer.set_job(job)

                # Fill application form and submit
                if hasattr(self.easy_applier_component, 'job_apply'):
                    self.easy_applier_component.job_apply(job)
                elif hasattr(self.easy_applier_component, '_fill_application_form'):
                    self.easy_applier_component._fill_application_form(job)
                self.write_to_file(job, "success")
                logger.info(f"Successfully applied to: '{job.title}' at '{job.company}'!")
                time.sleep(random.uniform(2.5, 4.0))

            except Exception as e:
                logger.error(f"Failed to apply for '{job.title}' at '{job.company}': {e}")
                if hasattr(self.easy_applier_component, '_discard_application'):
                    self.easy_applier_component._discard_application()
                self.write_to_file(job, "failed")
                continue

    def write_to_file(self, job, file_name):
        logger.debug(f"Writing job application result to file: {file_name}")
        pdf_path = Path(job.pdf_path).resolve()
        pdf_path = pdf_path.as_uri()
        data = {
            "company": job.company,
            "job_title": job.title,
            "link": job.link,
            "job_recruiter": job.recruiter_link,
            "job_location": job.location,
            "pdf_path": pdf_path
        }
        file_path = self.output_file_directory / f"{file_name}.json"
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([data], f, indent=4)
                logger.debug(f"Job data written to new file: {file_name}")
        else:
            with open(file_path, 'r+', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"JSON decode error in file: {file_path}")
                    existing_data = []
                existing_data.append(data)
                f.seek(0)
                json.dump(existing_data, f, indent=4)
                f.truncate()
                logger.debug(f"Job data appended to existing file: {file_name}")

    def get_base_search_url(self, parameters):
        logger.debug("Constructing base search URL")
        url_parts = []
        
        # Easy Apply filter (only if explicitly set to true in config)
        if parameters.get('easy_apply_only', False):
            url_parts.append("f_AL=true")
        
        # Remote (2) and Hybrid (3), excluding On-site (1)
        url_parts.append("f_WT=2%2C3")

        exp_dict = parameters.get('experienceLevel') or parameters.get('experience_level') or {}
        experience_levels = [str(i + 1) for i, (level, v) in enumerate(exp_dict.items()) if v]
        if experience_levels:
            url_parts.append(f"f_E={','.join(experience_levels)}")

        job_types = [key[0].upper() for key, value in parameters.get('jobTypes', {}).items() if value]
        if job_types:
            url_parts.append(f"f_JT={','.join(job_types)}")

        date_mapping = {
            "all time": "",
            "month": "f_TPR=r2592000",
            "week": "f_TPR=r604800",
            "24 hours": "f_TPR=r86400"
        }
        for k, v in date_mapping.items():
            if parameters.get('date', {}).get(k) and v:
                url_parts.append(v)
                break

        base_url = "&".join(url_parts)
        full_url = f"?{base_url}"
        logger.debug(f"Base search URL constructed: {full_url}")
        return full_url

    def next_job_page(self, position, location, job_page):
        logger.debug(f"Navigating to next job page: {position} in {location}, page {job_page}")
        pos_param = urllib.parse.quote_plus(str(position).strip())
        target_url = f"https://www.linkedin.com/jobs/search/{self.base_search_url}&keywords={pos_param}{location}&start={job_page * 25}"
        logger.info(f"Navigating to LinkedIn URL: {target_url}")
        self.driver.get(target_url)

    def extract_job_information_from_tile(self, job_tile):
        logger.debug("Extracting job information from tile")
        job_title, company, job_location, apply_method, link = "", "", "", "Easy Apply", ""
        try:
            # 1. Try modern dismiss button
            try:
                btn = job_tile.find_element(By.XPATH, ".//button[contains(@aria-label, 'Dismiss') and contains(@aria-label, 'job')]")
                aria = btn.get_attribute("aria-label") or ""
                job_title = aria.replace("Dismiss", "").replace("job", "").strip()
            except Exception:
                pass

            # 2. Extract company and location from tile text lines
            lines = [l.strip() for l in job_tile.text.splitlines() if l.strip()]
            if lines:
                if not job_title and len(lines) > 0:
                    job_title = lines[0]
                if len(lines) > 1:
                    company = lines[1]
                if len(lines) > 2:
                    job_location = lines[2]

            # 3. Check for data-job-id or data-occludable-job-id
            job_id = job_tile.get_attribute("data-job-id") or job_tile.get_attribute("data-occludable-job-id")
            if not job_id:
                try:
                    inner_id_el = job_tile.find_element(By.CSS_SELECTOR, "[data-job-id], [data-occludable-job-id]")
                    job_id = inner_id_el.get_attribute("data-job-id") or inner_id_el.get_attribute("data-occludable-job-id")
                except Exception:
                    pass

            # 4. Find title and link from standard elements if needed
            if not job_title or not link:
                title_el = None
                for sel in ['.job-card-list__title', '.job-card-container__link', 'a[class*="job-card-list__title"]', 'a[href*="/jobs/view/"]', 'strong']:
                    try:
                        title_el = job_tile.find_element(By.CSS_SELECTOR, sel)
                        if title_el.text.strip():
                            break
                    except NoSuchElementException:
                        continue

                if title_el:
                    if not job_title:
                        job_title = title_el.text.strip() or (title_el.get_attribute('aria-label') or "").strip()
                    href = title_el.get_attribute('href')
                    if href and '/jobs/view/' in href:
                        link = href.split('?')[0]

            if not link and job_id:
                link = f"https://www.linkedin.com/jobs/view/{job_id}/"

            if not company:
                for comp_class in ['job-card-container__primary-description', 'artdeco-entity-lockup__subtitle', 'job-card-container__company-name']:
                    try:
                        comp_el = job_tile.find_element(By.CLASS_NAME, comp_class)
                        if comp_el.text.strip():
                            company = comp_el.text.strip()
                            break
                    except NoSuchElementException:
                        continue

            if not job_location:
                try:
                    loc_el = job_tile.find_element(By.CLASS_NAME, 'job-card-container__metadata-item')
                    job_location = loc_el.text.strip()
                except NoSuchElementException:
                    pass

            tile_lower = job_tile.text.lower()
            if "applied" in tile_lower:
                apply_method = "Applied"
            else:
                apply_method = "Easy Apply"

            logger.debug(f"Job info extracted: '{job_title}' at '{company}', apply: '{apply_method}', link: '{link}'")
        except Exception as e:
            logger.warning(f"Error extracting title/company from tile: {e}")

        return job_title, company, job_location, link, apply_method

    def is_blacklisted(self, job_title, company, link):
        logger.debug(f"Checking if job is blacklisted: {job_title} at {company}")
        job_title_words = job_title.lower().split(' ')
        title_blacklisted = any(word in job_title_words for word in self.title_blacklist)
        company_blacklisted = company.strip().lower() in (word.strip().lower() for word in self.company_blacklist)
        link_seen = link in self.seen_jobs
        is_blacklisted = title_blacklisted or company_blacklisted or link_seen
        logger.debug(f"Job blacklisted status: {is_blacklisted}")

        return title_blacklisted or company_blacklisted or link_seen

    def is_already_applied_to_job(self, job_title, company, link):
        link_seen = link in self.seen_jobs
        if link_seen:
            logger.debug(f"Already applied to job: {job_title} at {company}, skipping...")
        return link_seen

    def is_already_applied_to_company(self, company):
        if not self.apply_once_at_company:
            return False

        output_files = ["success.json"]
        for file_name in output_files:
            file_path = self.output_file_directory / file_name
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        existing_data = json.load(f)
                        for applied_job in existing_data:
                            if applied_job['company'].strip().lower() == company.strip().lower():
                                logger.debug(
                                    f"Already applied at {company} (once per company policy), skipping...")
                                return True
                    except json.JSONDecodeError:
                        continue
        return False
