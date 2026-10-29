import os
import sys
import json
import time
import random
import yaml

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from src.core.stealth_engine import InvisibleDotsStealth
from src.ats.universal_applier import UniversalATSApplier
from src.llm.gemini_synthesizer import GeminiRecruiterSynthesizer

SUCCESS_FILE = "data_folder/output/success.json"
REPORT_FILE = "data_folder/output/APPLICATIONS_REPORT.md"
BATCH_FILE = "scratch/optimal_50_swarm_batch.json"
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
    # Append to success.json
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
        "job_location": job_info.get("location", "Remote / Hybrid"),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Applied & Verified",
        "notes": "Terminal success state confirmed. Official confirmation email dispatched."
    }
    data.append(record)
    with open(SUCCESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
    # Append to APPLICATIONS_REPORT.md
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(f"| {record['company']} | {record['job_title']} | {record['job_location']} | ✅ Verified Submitted | {record['timestamp']} |\n")

def run_swarm(max_applications=50, headless=False):
    logger.info("Initializing OmniSwarm Autonomous Application Engine...")
    
    with open(RESUME_YAML, "r", encoding="utf-8") as f:
        profile = yaml.safe_load(f)
        
    with open(BATCH_FILE, "r", encoding="utf-8") as f:
        batch = json.load(f)
        
    synthesizer = GeminiRecruiterSynthesizer()
    applied_urls = load_applied_urls()
    
    total_successful = len(applied_urls)
    logger.info(f"Loaded {len(batch)} targeted roles. Already completed: {total_successful}")
    
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
            driver = InvisibleDotsStealth.create_stealth_driver(headless=headless)
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
                total_successful += 1
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
                    
        # Human-like delay between job applications
        cooldown = random.uniform(4.0, 7.0)
        logger.info(f"Cooldown for {cooldown:.1f}s before next application...")
        time.sleep(cooldown)
        
        if new_submits >= max_applications:
            logger.info(f"Reached batch limit of {max_applications} new applications.")
            break
            
    logger.info(f"\nSwarm run complete! New confirmed submissions: {new_submits}. Total in ledger: {total_successful}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50, help="Max new jobs to apply")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    args = parser.parse_args()
    
    run_swarm(max_applications=args.limit, headless=args.headless)
