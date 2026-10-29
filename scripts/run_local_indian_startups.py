import os
import sys
import json
import time
import random
import yaml
from pathlib import Path
from loguru import logger

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ats.universal_applier import UniversalATSApplier
from src.core.stealth_engine import InvisibleDotsStealth
from src.llm.gemini_synthesizer import GeminiRecruiterSynthesizer

RESUME_YAML = "data_folder/plain_text_resume.yaml"
RESUME_PDF = "data_folder/resume.pdf"
SUCCESS_FILE = "data_folder/output/success.json"
REPORT_FILE = "data_folder/output/APPLICATIONS_REPORT.md"
BATCH_FILE = "scratch/priority_local_startups.json"

def load_applied_urls():
    applied = set()
    if os.path.exists(SUCCESS_FILE):
        try:
            with open(SUCCESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    url = item.get("link") or item.get("url")
                    if url:
                        applied.add(url.strip())
        except Exception as e:
            logger.warning(f"Could not parse success.json: {e}")
    return applied

def record_success(job_info):
    data = []
    if os.path.exists(SUCCESS_FILE):
        try:
            with open(SUCCESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
            
    record = {
        "company": job_info["company"],
        "job_title": job_info["title"],
        "link": job_info["url"],
        "job_location": job_info.get("location", "India / Remote"),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Applied & Verified",
        "notes": "Terminal success state confirmed. Official confirmation email dispatched."
    }
    data.append(record)
    with open(SUCCESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(f"| {record['company']} | {record['job_title']} | {record['job_location']} | ✅ Verified Submitted | {record['timestamp']} |\n")

def main():
    logger.info("==================================================================")
    logger.info("   LAUNCHING LOCAL INDIAN & LOW-SCALE REMOTE STARTUPS WORKER     ")
    logger.info("==================================================================")

    with open(RESUME_YAML, "r", encoding="utf-8") as f:
        profile = yaml.safe_load(f)
        
    with open(BATCH_FILE, "r", encoding="utf-8") as f:
        batch = json.load(f)
        
    synthesizer = GeminiRecruiterSynthesizer()
    applied_urls = load_applied_urls()
    
    logger.info(f"Loaded {len(batch)} targeted roles. Total in success ledger: {len(applied_urls)}")
    
    new_submits = 0
    for idx, job in enumerate(batch):
        url = job["url"].strip()
        company = job["company"]
        title = job["title"]
        
        if url in applied_urls:
            logger.info(f"Skipping already applied: {company} - {title}")
            continue
            
        logger.info(f"\n==========================================")
        logger.info(f"[{idx+1}/{len(batch)}] Processing: {company} - {title}")
        logger.info(f"URL: {url}")
        logger.info(f"==========================================")
        
        driver = None
        try:
            driver = InvisibleDotsStealth.create_stealth_driver(headless=True)
            applier = UniversalATSApplier(
                driver=driver,
                resume_path=RESUME_PDF,
                profile_data=profile,
                synthesizer=synthesizer
            )
            
            success = applier.apply(
                job_title=title,
                company=company,
                target_url=url
            )
            
            if success:
                logger.info(f"🎉 SUCCESS: Verified application for {company} - {title}")
                record_success(job)
                applied_urls.add(url)
                new_submits += 1
            else:
                logger.warning(f"❌ Failed to reach terminal confirmation for {company} - {title}")
                
        except Exception as e:
            logger.error(f"Error applying to {company} - {title}: {e}")
            
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
                    
        cd = random.uniform(4.0, 7.5)
        logger.info(f"Cooldown for {cd:.1f}s before next application...")
        time.sleep(cd)
        
    logger.info("==================================================================")
    logger.info(f"Local & Remote Startups Worker complete! Newly Submitted: {new_submits}")
    logger.info("==================================================================")

if __name__ == "__main__":
    main()
