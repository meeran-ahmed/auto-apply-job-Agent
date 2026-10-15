# Auto Apply Job Agent (OmniSwarm Edition)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Status: Active](https://img.shields.io/badge/Status-Open%20Source-success.svg)](https://github.com/meeran-ahmed/auto-apply-job-Agent)

An autonomous, multi-agent job application engine designed to help job seekers apply to matching tech positions across the web with zero manual intervention. Built on top of the AIHawk foundation and enhanced into a decentralized multi-agent swarm (**OmniSwarm**) by **Meeran Ahmed**.

---

## Why This Exists

Applying for jobs today is broken. Job seekers spend 4 to 8 hours a day manually re-typing the same contact details, uploading the same resume, answering repetitive screening questions, and getting redirected across multiple portals.

**Auto Apply Job Agent** solves this by orchestrating specialized AI worker agents that:
1. **Scout Opportunities**: Monitor live remote feeds across the global internet (not just LinkedIn).
2. **Handle Dual-Tier Applications**: Seamlessly submit LinkedIn Easy Apply jobs and follow external apply links to company career portals.
3. **Bypass Intermediaries & Complete ATS Forms**: Automatically fill and submit applications on **Greenhouse**, **Lever**, **Ashby**, **Workday**, **SmartRecruiters**, and generic career pages.
4. **Attach Candidate Assets**: Automatically upload PDF resumes, portfolio URLs, GitHub repositories, and phone credentials.
5. **Generate Real-Time Audit Ledgers**: Compile an executive Markdown report (`APPLICATIONS_REPORT.md`) and structured JSON ledger (`success.json`) detailing every submitted job, timestamp, and company link.

---

## Architecture: How OmniSwarm Works

```
                                 +-----------------------+
                                 |   SwarmOrchestrator   |
                                 +-----------+-----------+
                                             |
            +--------------------------------+--------------------------------+
            |                                |                                |
            v                                v                                v
+-----------------------+        +-----------------------+        +-----------------------+
|   RemotePortalAgent   |        |   LinkedInApplier     |        |     ReporterAgent     |
|   (Discovery Scout)   |        |   (Dual-Tier Engine)  |        |   (Audit & Ledger)    |
+-----------+-----------+        +-----------+-----------+        +-----------+-----------+
            |                                |                                ^
            | Discovers feeds                | Redirects to                   | Logs results
            v                                v                                |
+--------------------------------------------------------+                    |
|                        ATSAgent                        |--------------------+
|  Detects: Greenhouse / Lever / Ashby / Workday / Forms |
|  Fills: Personal Info + Resume + Custom Screening Qs   |
+--------------------------------------------------------+
```

### Specialized Agents:
- **`RemotePortalAgent`**: Connects to live job endpoints (Jobicy, Himalayas, Remotive, RemoteOK, Arbeitnow) to discover remote engineering positions without requiring account logins.
- **`ATSAgent`**: Intercepts company career portals, switches into nested iframes, attaches resumes, fills contact fields, and clicks submission triggers.
- **`ReporterAgent`**: Thread-safe central reporting unit. Logs every success, skip, and blocker to generate structured executive summaries.
- **`AIHawkJobManager & EasyApplier`**: High-precision LinkedIn automation that completes Easy Apply flows and navigates external employer forms.

---

## Supported Platforms & ATS Portals

| Platform / System | Application Method | Auto-Fill Capabilities |
| :--- | :--- | :--- |
| **LinkedIn** | Easy Apply & External Redirection | Full contact info, screening answers, phone prefix |
| **Greenhouse (`greenhouse.io`)** | Direct / Embedded ATS | Resume upload, first/last name, LinkedIn/GitHub/Portfolio URLs |
| **Lever (`lever.co`)** | Direct / Embedded ATS | Resume upload, personal details, custom text inputs |
| **Ashby (`ashbyhq.com`)** | Direct / Embedded ATS | Resume upload, email, contact data, dropdown select |
| **Jobicy / RemoteOK / Himalayas** | Global Feed Aggregation | Direct company ATS link resolution |
| **Generic Career Portals** | Universal DOM Heuristics | Multi-field text injection, file uploaders, submit triggers |

---

## Getting Started

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- Google Chrome browser installed
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/meeran-ahmed/auto-apply-job-Agent.git
cd auto-apply-job-Agent
```

### 3. Create a Virtual Environment & Install Dependencies
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

## Free Gemini API Key Setup (No Credit Card Required)

This project uses Google's **Gemini 1.5 Flash** model to answer custom screening questions intelligently and reliably. Anyone can obtain a free API key in under 60 seconds:

1. Open your browser and navigate to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Sign in using any standard Google / Gmail account.
3. Click the blue **"Create API key"** button.
4. Select or create a free project, then copy the generated API key (starts with `AIzaSy...`).
5. Set up your local secrets file:
   ```bash
   cp data_folder/secrets.yaml.template data_folder/secrets.yaml
   ```
6. Paste your key inside `data_folder/secrets.yaml`:
   ```yaml
   llm_api_key: "AIzaSyYourGeneratedGoogleAIStudioKeyHere"
   ```

> **Note**: `data_folder/secrets.yaml` is strictly ignored by `.gitignore` to ensure your credentials are never committed.

---

## Configuration

### 1. Configure Your Resume & Personal Data
```bash
cp data_folder/plain_text_resume.yaml.template data_folder/plain_text_resume.yaml
```
Open `data_folder/plain_text_resume.yaml` and enter your details:
- Name, email, phone number (with country code, e.g., `+91`), address, city, and zip code.
- GitHub profile, LinkedIn profile, and live portfolio website URL.
- Education, past experience, and key technical skills.

Place your PDF resume inside the `data_folder/` directory:
```
data_folder/resume.pdf
```

### 2. Configure Your Search Targets
```bash
cp data_folder/config.yaml.template data_folder/config.yaml
```
Customize your job search parameters:
```yaml
remote: true

positions:
  - Full Stack Developer
  - Frontend Developer
  - React Developer
  - Software Engineer
  - Solutions Engineer

locations:
  - Remote
  - Worldwide
  - India
  - United States

titleBlacklist:
  - Senior
  - Staff
  - Principal
  - Architect
  - Director
  - Onsite
```

---

## 🖥️ 1-Click Desktop GUI & Launchers (No Terminal Needed!)

Non-technical users can launch OmniSwarm with a single click:

- **Windows**: Double-click `launcher.bat` to launch the Dark Mode Desktop GUI.
- **macOS / Linux**: Run `./launcher.sh` in terminal.
- **Python command**:
  ```bash
  python gui_main.py
  ```

### GUI Features:
- 👤 **Candidate Profile Tab**: Easily enter contact info, portfolio link, and upload your PDF resume.
- 🔑 **Keys Tab**: Save your free Google Gemini API key securely.
- ⚡ **Dashboard Tab**: Pick between Auto-Scout Swarm or Custom Excel Spreadsheet, set application limits, watch live console logs, and click to view your Markdown report instantly.

---

## 📱 1-Click Mobile & Tablet Cloud Runner (Google Colab)

Don't have a computer? You can run OmniSwarm directly from your **iPhone, Android, iPad, or Chromebook**:
1. Open the [`OmniSwarm_Mobile_Runner.ipynb`](OmniSwarm_Mobile_Runner.ipynb) in **Google Colab**.
2. Run Step 1 (installs headless Chromium in Google's cloud sandbox for free).
3. Upload your resume and spreadsheet in Step 2.
4. Tap Step 3 to start applying! OmniSwarm automatically downloads your completed application report when done.

---

## Running from the Terminal (CLI)

### Option A: Custom Excel / CSV Batch Auto-Apply
Have a curated list of jobs? Drop an Excel (`.xlsx`, `.xls`) or CSV spreadsheet with job links, and the swarm will process and submit applications to every listed URL:
```bash
python swarm_main.py --mode excel --file data_folder/jobs_template.xlsx
```
*(If `--file` is omitted, the agent will automatically find and process any `.xlsx` or `.csv` file in `data_folder/`)*. Ready-to-use templates are included at [`data_folder/jobs_template.xlsx`](file:///d:/job%20auto/aihawk/data_folder/jobs_template.xlsx) and [`data_folder/jobs_template.csv`](file:///d:/job%20auto/aihawk/data_folder/jobs_template.csv).

### Option B: Global Remote Swarm (No LinkedIn login needed)
Dispatches the swarm across remote job boards and company ATS endpoints:
```bash
python swarm_main.py --mode swarm --limit 50
```

### Option C: All Channels (Full Spectrum)
Runs the remote discovery swarm first, followed by LinkedIn automation:
```bash
python swarm_main.py --mode all --limit 50
```


## Use with AI Agents (Antigravity, Cursor, Claude Code, Codex)

This repository includes a pre-packaged **Agent Skill** (`.agents/skills/auto-job-applier/SKILL.md` and `skills/auto-job-applier/SKILL.md`), allowing any modern AI coding assistant to operate the swarm on your behalf.

### Supported Coding Environments:
- **Google Antigravity IDE**: The agent automatically detects the skill in `.agents/skills/auto-job-applier/`. Simply ask: *"Apply for remote React jobs in the background."*
- **Cursor IDE / Claude Code**: The skill is indexed under `skills/auto-job-applier/SKILL.md`. Prompt your assistant with: *"Run the job applier swarm and generate an application report."*
- **OpenAI Codex / Windsurf**: Run tasks using natural language prompts against `swarm_main.py`.

---

## Executive Audit Report

After execution, open `data_folder/output/APPLICATIONS_REPORT.md` to view your application metrics:

```markdown
# 🚀 OmniSwarm Automated Job Applications Report
**Candidate**: Meeran Ahmed R.
**Total Processed**: 82 | **Successfully Applied**: 35

## 📊 Executive Summary
| Metric | Count | Percentage |
| :--- | :--- | :--- |
| **Total Applied** | **35** | **42.7%** |
| **Skipped (Blacklisted / Applied Before)** | 47 | 57.3% |
| **Failed (Unresolved Blockers)** | 0 | 0.0% |

## 📝 Submitted Job Applications
| # | Job Title | Company | Platform | Applied At | Link |
| :- | :--- | :--- | :--- | :--- | :--- |
| 1 | Technical Lead | Solace | Greenhouse | 2026-10-15 | [View Job](...) |
| 2 | Product Engineer | Help Scout | Greenhouse | 2026-10-15 | [View Job](...) |
| 3 | Software Engineer | Samsara | Greenhouse | 2026-10-15 | [View Job](...) |
```

A machine-readable copy is also saved to `data_folder/output/success.json` for custom analytics or CRM tracking.

---

## Ethical Automation & Best Practices

1. **Be Honest with Credentials**: Ensure your `plain_text_resume.yaml` accurately portrays your skills, experience, and availability.
2. **Review Target Positions**: Use `titleBlacklist` and `companyBlacklist` to avoid submitting to irrelevant or spam listings.
3. **Pacing & Rate Limits**: Default delays are intentionally built into the browser controllers to avoid hammering employer servers.
4. **Follow Up Responsibly**: Regularly check your application email for confirmations and assessment links.

---

## Contributing

Contributions from the developer community are welcome!
1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/new-ats-applier`).
3. Commit your changes (`git commit -m "Add support for BambooHR ATS"`).
4. Push to the branch (`git push origin feature/new-ats-applier`).
5. Open a Pull Request.

---

## License & Credits

- **Author & Swarm Architect**: [Meeran Ahmed](https://github.com/meeran-ahmed)
- **Base Project**: Derived and enhanced from [Auto_Jobs_Applier_AIHawk](https://github.com/feder-cr/Auto_Jobs_Applier_AIHawk).
- **License**: Released under the [MIT License](LICENSE).
