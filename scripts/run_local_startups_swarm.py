import os
import sys
import json
import time
import random
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from src.core.stealth_engine import InvisibleDotsStealth
from src.ats.universal_applier import UniversalATSApplier
from src.llm.gemini_synthesizer import GeminiRecruiterSynthesizer

SUCCESS_FILE = "data_folder/output/success.json"
REPORT_FILE = "data_folder/output/APPLICATIONS_REPORT.md"
BATCH_FILE = "scratch/local_indian_startups_batch.json"
RESUME_YAML = "data_folder/plain_text_resume.yaml"
RESUME_PDF = "data_folder/resume.pdf"

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
        "notes": "OmniSwarm Local Startup Engine verified submission."
    }
    data.append(record)
    with open(SUCCESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(f"| {record['company']} | {record['job_title']} | {record['job_location']} | ✅ Verified Submitted | {record['timestamp']} |\n")

def run_local_swarm():
    logger.info("Starting Dedicated Local Indian & Remote Startup Swarm Worker...")
    with open(RESUME_YAML, "r", encoding="utf-8") as f:
        profile = yaml.safe_load(f)
    with open(BATCH_FILE, "r", encoding="utf-8") as f:
        batch = json.load(f)
        
    synthesizer = GeminiRecruiterSynthesizer()
    applied_urls = load_applied_urls()
    
    for idx, job in enumerate(batch):
        url = job["url"].strip()
        company = job["company"]
        title = job["title"]
        
        if url in applied_urls:
            logger.info(f"Skipping already applied: {company} - {title}")
            continue
            
        logger.info(f"\n==========================================")
        logger.info(f"[LOCAL STARTUP {idx+1}/{len(batch)}] {company} - {title}")
        logger.info(f"Location: {job.get('location')} | URL: {url}")
        logger.info(f"==========================================")
        
        driver = None
        try:
            driver = InvisibleDotsStealth.create_stealth_driver(headless=False)
            applier = UniversalATSApplier(
                driver=driver,
                resume_path=RESUME_PDF,
                profile_data=profile,
                synthesizer=synthesizer
            )
            success = applier.apply(job_title=title, company=company, target_url=url)
            if success:
                logger.info(f"🎉 SUCCESS: Verified local startup application for {company} - {title}")
                record_success(job)
                applied_urls.add(url)
            else:
                logger.warning(f"❌ Failed to reach terminal confirmation for {company} - {title}")
        except Exception as e:
            logger.error(f"Error on {company} - {title}: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        time.sleep(random.uniform(4.0, 7.0))

if __name__ == "__main__":
    run_local_swarm()

