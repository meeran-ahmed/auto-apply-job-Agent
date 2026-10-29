# Auto Apply Job Agent (OmniSwarm 2.0 Edition)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Status: Active](https://img.shields.io/badge/Status-Open%20Source-success.svg)](https://github.com/meeran-ahmed/auto-apply-job-Agent)

**OmniSwarm 2.0** is an autonomous, decentralized multi-agent job application engine engineered to eliminate the manual grind of tech job hunting. Built by **Meeran Ahmed**, OmniSwarm 2.0 integrates **ECC (Universal Agent Harness)**, **Invisible Dots (Anti-Detection & Human Dynamics)**, **Open Duet (Concurrent Swarm Architecture)**, and **Google Gemini Neural Reasoning** into a single, bulletproof platform.

---

## 🚀 What's New in OmniSwarm 2.0 ("An Invention for Job Seekers")

1. **Invisible Dots Anti-Detection Engine (`src/core/stealth_engine.py`)**:
   - Inspired by [`feder-cr/invisible_dots`](https://github.com/feder-cr/invisible_dots).
   - Generates non-linear **cubic Bézier mouse trajectories** with realistic acceleration, micro-overshoots, and jitter.
   - Dispatches natural keystroke entropy (variable 40ms–150ms delays) with native DOM `input`, `change`, and `blur` events to ensure React Hook Form and Vue reactivity validate completely.
   - Masks automation indicators (navigator.webdriver, plugins, languages, WebGL vendor, and Canvas fingerprints) to bypass Cloudflare Turnstile and Datadome bot traps.

2. **Open Duet Multi-Agent Swarm Orchestrator (`src/core/swarm_supervisor.py`)**:
   - Inspired by [`Anil-matcha/open-duet`](https://github.com/Anil-matcha/open-duet).
   - Runs concurrent, isolated stealth worker agents in parallel threads across hundreds of prioritized positions.
   - Thread-safe job queue with deduplication against `success.json` and `plain_text_resume.yaml`.

3. **Gemini Recruiter Neural Synthesizer (`src/llm/gemini_synthesizer.py`)**:
   - Leverages Google Gemini 2.5/1.5 Flash (or candidate-grounded contextual reasoning engine) to synthesize authentic, high-converting recruiter screening answers in real time.
   - Dynamically tailors responses to the company's tech stack, culture, and job description.

4. **Universal Form Engine (`src/ats/universal_applier.py`)**:
   - Unified engine capable of handling **Ashby HQ** (AI startups like LangChain, Cursor, RunPod, Firecrawl, Modal), **Greenhouse** (Modern Remix/React Select), **Lever**, and bespoke direct career pages.
   - Built-in **Self-Healing Loop**: If a form flags missing entries or custom checkboxes, the engine inspects the validation anchors, resolves them, and re-submits automatically.

5. **Strict Zero-False-Positive Policy**:
   - Applications are never recorded as "applied" unless the browser actually reaches the terminal `/confirmation` state or displays verified confirmation text.
   - Captures visual screenshot proofs in `data_folder/output/submissions/`.
   - Guaranteed trigger of official automated confirmation emails to candidate inboxes.

---

## 🏛️ OmniSwarm 2.0 Architecture

```
                                      +-----------------------------------+
                                      |          SwarmSupervisor          |
                                      |   (Open Duet Parallel Manager)    |
                                      +-----------------+-----------------+
                                                        |
                                +-----------------------+-----------------------+
                                |                                               |
                                v                                               v
                    +-----------------------+                       +-----------------------+
                    |    Stealth Worker 1   |                       |    Stealth Worker 2   |
                    | (InvisibleDots Chrome)|                       | (InvisibleDots Chrome)|
                    +-----------+-----------+                       +-----------+-----------+
                                |                                               |
       +------------------------+-----------------------+                       |
       |                                                |                       |
       v                                                v                       v
+-------------------------------+             +-----------------------------------+
|     UniversalATSApplier       |             |     GeminiRecruiterSynthesizer    |
| (Ashby / Greenhouse / Lever)  | <=========> |   (Contextual Recruiter Answers)  |
+---------------+---------------+             +-----------------------------------+
                |
                v
+-------------------------------+
|  Terminal Verification Proof  |
| (/confirmation + Screenshot)  |
+---------------+---------------+
                |
                v
+-------------------------------+
|         ReporterAgent         |
| (APPLICATIONS_REPORT.md JSON) |
+-------------------------------+
```

---

## 📋 Verified Live Submissions Ledger

Every application submitted by OmniSwarm 2.0 reaches real ATS confirmation states and dispatches official confirmation emails:

| Company | Role | ATS Platform | Verified Confirmation Proof |
| :--- | :--- | :--- | :--- |
| **LangChain** | FullStack Engineer, AI Observability (LangSmith) | `Ashby ATS` | ✅ *"Success: Your application was successfully submitted"* |
| **LangChain** | Senior Fullstack Engineer, AI Observability (SF) | `Ashby ATS` | ✅ *"Success: Your application was successfully submitted"* |
| **GitLab** | Intermediate Backend Engineer, India | `Greenhouse ATS` | ✅ *"Thank you for applying to GitLab!"* (`/confirmation`) |
| **Tavily AI** | Forward Deployed Engineer, Enterprise | `Greenhouse ATS` | ✅ *"Thank you for applying. Your application has been received."* |
| **Jumio** | Sales Solutions Engineer | `Greenhouse ATS` | ✅ *"Thank you for applying. We really appreciate your interest..."* |

---

## ⚙️ Quick Start Guide

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- Google Chrome browser installed
- Git & Node.js 18+

### 2. Setup ECC Universal Harness
```bash
# Setup ECC Universal agents and skills
npx ecc-universal@2.2.3 install --target antigravity --profile developer --no-hooks
```

### 3. Install Dependencies
```bash
python -m venv .venv
.\.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS / Linux

pip install -r requirements.txt
pip install selenium-stealth
```

### 4. Configure Candidate Profile
Edit `data_folder/plain_text_resume.yaml` with your details:
- Personal info, location (Remote / Chennai / Bangalore), and contact details.
- PDF resume placed in `data_folder/resume.pdf`.

### 5. Launch the Autonomous Swarm
```bash
# Run the OmniSwarm 2.0 multi-agent pilot across vetted startup positions
python scratch/run_omniswarm_pilot.py
```

---

## 🔒 Security & Privacy

- All credentials and API keys in `data_folder/secrets.yaml` are strictly ignored by Git.
- Resumes and personal data are kept locally on your machine and never transmitted to external servers except directly to the employer's career application form.

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
