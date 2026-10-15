---
name: auto-job-applier
description: Autonomous Multi-Agent Job Application Engine (OmniSwarm). Automatically discovers matching tech positions across global remote job feeds and LinkedIn, auto-populates candidate details and resumes, navigates external Applicant Tracking Systems (Greenhouse, Lever, Ashby, Workday), submits applications autonomously, and compiles comprehensive Markdown and JSON audit reports.
---

# Auto Job Applier (OmniSwarm) - Agent Skill

This skill enables any AI agent (Google Antigravity, Claude Code, Cursor, OpenAI Codex, or Windsurf) to autonomously configure, execute, and monitor the multi-agent job application swarm on behalf of the user.

## Core Capabilities
1. **Multi-Feed Discovery**: Scans live APIs and RSS feeds across Jobicy, Himalayas, Remotive, RemoteOK, and Arbeitnow for matching tech roles.
2. **Dual-Tier LinkedIn Engine**: Applies to LinkedIn Easy Apply positions and follows external apply buttons to company career portals.
3. **Universal ATS Autonomous Filler**: Detects and auto-submits applications on Greenhouse, Lever, Ashby, Workday, SmartRecruiters, and generic web forms.
4. **Zero-Touch Auto-Fill**: Injects candidate personal information, phone country prefix, portfolio URLs, GitHub links, and attaches PDF resumes automatically.
5. **Real-Time Audit Ledger**: Thread-safe reporting agent generates `data_folder/output/APPLICATIONS_REPORT.md` and `data_folder/output/success.json`.

---

## Prerequisites & Setup

### 1. Free Gemini API Key (Google AI Studio)
The agent uses Google Gemini 1.5 Flash for answering custom employer questions and form fields.
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Sign in with any standard Google account.
3. Click **Create API Key**.
4. Create `data_folder/secrets.yaml` and set:
   ```yaml
   llm_api_key: "AIzaSy..."
   ```

### 2. Candidate Profile & Resume
1. Copy `data_folder/plain_text_resume.yaml.template` to `data_folder/plain_text_resume.yaml`.
2. Populate personal contact details, education, past roles, and skills.
3. Place the PDF resume in `data_folder/resume.pdf`.

### 3. Target Search Configuration
1. Copy `data_folder/config.yaml.template` to `data_folder/config.yaml`.
2. Define target job titles (`positions`), desired locations (`locations`), and remote preferences (`remote: true`).

---

## Agent Execution Workflows

### Mode A: Global Remote Swarm (No LinkedIn Login Required)
Dispatches the remote scout agent across worldwide tech portals and submits applications directly to company ATS endpoints:
```bash
python swarm_main.py --mode swarm --limit 50
```

### Mode B: LinkedIn Dual-Tier Apply
Launches browser automation on LinkedIn to process Easy Apply listings and redirect external positions to company ATS career portals:
```bash
python swarm_main.py --mode linkedin
```

### Mode C: Full Spectrum Swarm
Executes both the global remote swarm and LinkedIn automation sequentially:
```bash
python swarm_main.py --mode all --limit 50
```

---

## Agent Inspection & Monitoring

When executing this skill in the background:
- **Ledger Verification**: Inspect `data_folder/output/success.json` for submitted records.
- **Executive Report**: Read `data_folder/output/APPLICATIONS_REPORT.md` to review total processed count, success rates, and direct links to submitted applications.
