# InterviewMate AI – Your Personal AI Interview Trainer

> **B.Tech Information Technology College Project**
> AI-powered interview preparation platform using Python, Flask, SQLite, IBM watsonx.ai (IBM Granite), and Retrieval-Augmented Generation.

---

## Table of Contents

1. [What This Project Does](#1-what-this-project-does)
2. [Quick Start (5 Steps)](#2-quick-start-5-steps)
3. [IBM watsonx.ai Credentials Setup](#3-ibm-watsonxai-credentials-setup)
4. [Running the App](#4-running-the-app)
5. [How to Use](#5-how-to-use)
6. [Project Structure](#6-project-structure)
7. [Features](#7-features)
8. [URL Map](#8-url-map)
9. [Responsible AI Notice](#9-responsible-ai-notice)
10. [Running the Tests](#10-running-the-tests)
11. [Troubleshooting](#11-troubleshooting)
12. [CLI Utilities](#12-cli-utilities)

---

## 1. What This Project Does

InterviewMate AI is a web application that lets students practise technical and HR job interviews with an AI interviewer powered by IBM Granite. In a single session the app:

1. Accepts a job role, interview type, difficulty and question count from the student.
2. Retrieves role-specific topics from a local JSON knowledge base using a keyword-scoring RAG pipeline.
3. Sends those topics plus a structured prompt to **IBM Granite** (`ibm/granite-3-1-8b-base`) to generate fresh interview questions.
4. Displays the questions to the student with a countdown timer.
5. Sends each answer back to IBM Granite for evaluation — returning a score out of 10, plus correctness, clarity, completeness, strengths, improvement suggestions, and a model answer.
6. Persists the entire session (questions, answers, scores) to a local SQLite database.
7. Shows an aggregate dashboard with total sessions, average score, history table, and per-role performance.

No answers are hardcoded. All AI output comes from real IBM Granite API calls.

---

## 2. Quick Start (5 Steps)

Open a terminal (PowerShell on Windows) and run these commands:

```powershell
# Step 1 – Go to the project folder
cd path\to\InterviewMate-AI

# Step 2 – Create a virtual environment
python -m venv .venv

# Step 3 – Activate it (Windows)
.venv\Scripts\activate

# Step 4 – Install all dependencies
pip install -r requirements.txt

# Step 5 – Copy the credentials template
copy .env.example .env
```

Then open `.env` and fill in your real IBM credentials (see Section 3), and run:

```powershell
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 3. IBM watsonx.ai Credentials Setup

You need four values. Open the `.env` file and replace the placeholder text:

```ini
WATSONX_API_KEY=your_real_api_key_here
WATSONX_PROJECT_ID=your_real_project_id_here
WATSONX_URL=https://eu-de.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-3-1-8b-base
```

### How to get your IBM Cloud API Key

1. Log in to https://cloud.ibm.com
2. Click your **profile icon** (top-right) → **IBM Cloud API keys**
3. Click **Create an IBM Cloud API key**
4. Give it a name like `interviewmate-key` and click **Create**
5. **Copy the key immediately** — it is shown only once

### How to get your watsonx.ai Project ID

1. Go to https://dataplatform.cloud.ibm.com and log in
2. Click **Projects** → open (or create) a project
3. Click the **Manage** tab → **General**
4. Copy the **Project ID** shown there

### Choosing your region URL

| IBM Cloud Region | WATSONX_URL |
|---|---|
| Frankfurt (EU) | `https://eu-de.ml.cloud.ibm.com` |
| Dallas (US-South) | `https://us-south.ml.cloud.ibm.com` |
| Tokyo (AP-North) | `https://jp-tok.ml.cloud.ibm.com` |

> **Security:** The `.env` file is already listed in `.gitignore`. Never commit it to GitHub or share it.

### Verify your credentials before running the app

```powershell
python -m services.granite_service --test
```

If the connection is working you will see `[PASSED]` and a short reply from the model. If you see `[FAILED]` the error message explains exactly what to fix.

---

## 4. Running the App

```powershell
# Make sure the virtual environment is activated first
.venv\Scripts\activate

python app.py
```

Expected output:

```
[OK] IBM watsonx.ai config: model=ibm/granite-3-1-8b-base, url=https://eu-de.ml.cloud.ibm.com
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

If your `.env` has placeholder values instead of real credentials, you will see a `WARNING` listing the missing variables. The app still starts but IBM Granite calls will fail.

Open **http://localhost:5000** in your browser.

---

## 5. How to Use

### Step-by-step walkthrough

| Step | Page | What happens |
|------|------|-------------|
| 1 | Home (`/`) | Click **Start Practice Interview** |
| 2 | Setup (`/setup`) | Enter your name, choose role, type, difficulty, question count → click **Generate Questions** |
| 3 | Waiting | IBM Granite generates questions (10–30 seconds) |
| 4 | Interview (`/interview/<id>`) | Answer each question in the text area; watch the timer and progress bar |
| 5 | Submission | Click **Submit All Answers**; IBM Granite evaluates each answer (20–60 seconds) |
| 6 | Results (`/results/<id>`) | See your score ring, per-question feedback accordion, and model answers |
| 7 | Dashboard (`/dashboard`) | View total sessions, average score, history table, per-role breakdown |

### Supported choices

| Dimension | Options |
|-----------|---------|
| Job Role | Java Developer · Python Developer · Web Developer · Data Analyst · Software Engineer |
| Interview Type | Technical · HR · Mixed |
| Difficulty | Beginner · Intermediate · Advanced |
| Questions | 3 · 5 · 7 · 10 |

---

## 6. Project Structure

```
InterviewMate-AI/
│
├── app.py                        ← Entry point — run this to start the server
├── config.py                     ← All settings, reads from .env
├── requirements.txt              ← Python dependencies
├── .env                          ← Your credentials (fill this in, never commit)
├── .env.example                  ← Credentials template
├── .gitignore
│
├── database/
│   └── db.py                     ← SQLite schema, migration, all data helpers
│
├── services/
│   ├── granite_service.py        ← IBM watsonx.ai SDK — generates questions,
│   │                                evaluates answers, handles all API errors
│   ├── rag_service.py            ← RAG pipeline — keyword-scored retrieval
│   │                                from JSON knowledge base
│   └── ai_service.py             ← Re-exports from granite_service (compatibility)
│
├── knowledge_base/               ← Local knowledge base (5 JSON files)
│   ├── java_developer.json
│   ├── python_developer.json
│   ├── web_developer.json
│   ├── data_analyst.json
│   └── software_engineer.json
│
├── routes/
│   ├── __init__.py
│   ├── interview.py              ← All 6 interview flow routes
│   └── dashboard.py              ← Dashboard route
│
├── static/
│   ├── css/style.css             ← Full design system (purple/white SaaS theme)
│   └── js/interview.js           ← Timer, progress bar, unsaved-changes guard
│
├── templates/                    ← Jinja2 HTML templates
│   ├── base.html                 ← Shared navbar, footer, mobile hamburger
│   ├── index.html                ← Landing page
│   ← setup.html                  ← Interview configuration form
│   ├── interview.html            ← Answer form with timer
│   ├── results.html              ← Score ring + feedback accordion
│   └── dashboard.html            ← Stats cards + history table
│
├── tests/
│   ├── test_rag_db.py            ← 100 RAG + database tests
│   └── test_integration.py       ← 75 integration tests (Flask + mocked IBM SDK)
│
└── docs/
    ├── ARCHITECTURE.md           ← System design, diagrams, tech stack
    ├── TESTING_REPORT.md         ← Full test results with pass/fail counts
    └── PRESENTATION.md           ← 2–3 minute demo script
```

---

## 7. Features

| Feature | Detail |
|---------|--------|
| **AI Question Generation** | IBM Granite generates unique questions every session based on role, type, and difficulty |
| **RAG Knowledge Base** | 5 JSON files (10–15 questions each at 3 difficulty levels) provide domain context that guides the AI |
| **7-Dimension Evaluation** | Score /10 · Correctness · Clarity · Completeness · Strengths · Improvements · Sample answer |
| **SQLite Persistence** | Sessions, questions, answers, and scores survive server restarts |
| **Progress Dashboard** | Total sessions, total answers evaluated, average score, session history, per-role breakdown |
| **30-minute Timer** | Countdown clock with animated progress; auto-submits when time expires |
| **Progress Bar** | Live indicator: X of Y questions answered |
| **Unsaved-changes Guard** | Browser warns if you try to navigate away mid-interview |
| **Score Ring** | Animated SVG circle coloured green (≥7), amber (≥4), or red (<4) |
| **Feedback Accordion** | Per-question collapsible panel with 4-cell feedback grid |
| **Student Name** | Optional name field stored and shown in history and results |
| **Responsible AI Notice** | Displayed on interview and results pages |
| **Credential Validation** | Startup check for missing or placeholder `.env` values |
| **Connection Test CLI** | `python -m services.granite_service --test` |
| **Model List CLI** | `python -m services.granite_service --list-models` |
| **RAG Report CLI** | `python -m services.rag_service --report "Role" Type Difficulty` |

---

## 8. URL Map

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/` | Home / landing page |
| `GET` | `/setup` | Interview configuration form |
| `POST` | `/generate` | Process setup form, generate questions, create DB session |
| `GET` | `/interview/<id>` | Interview page — answer form with timer |
| `POST` | `/submit/<id>` | Evaluate answers, complete session, redirect to results |
| `GET` | `/results/<id>` | Results page — scores and feedback |
| `GET` | `/dashboard` | Dashboard — stats and history |

---

## 9. Responsible AI Notice

> **AI-generated scores are estimates for practice purposes only and do not represent actual hiring decisions.**

- Answers are processed by **IBM watsonx.ai** using the **IBM Granite** foundation model.
- All data (sessions, answers, scores) is stored **only in the local SQLite database** on your machine.
- API credentials are stored in your local `.env` file and are **never transmitted to third parties**.
- This tool is designed for **educational and self-improvement purposes** only.
- The evaluation criteria (score, correctness, clarity, completeness, strengths, improvements) are AI-generated estimates and may not reflect the standards of any specific employer.

---

## 10. Running the Tests

### RAG and database tests (no IBM credentials needed)

```powershell
python tests/test_rag_db.py
```

Expected: `RESULT: ALL TESTS PASSED` — 100 checks across 16 test sections.

### Integration tests (Flask + mocked IBM SDK — no real credentials needed)

```powershell
python tests/test_integration.py
```

Expected: `RESULT: ALL INTEGRATION TESTS PASSED [OK]` — 75 checks across 12 test areas.

> The IBM SDK prints some diagnostic lines to stderr when exception objects are constructed during the mock tests. This is expected behaviour of the SDK's internal logging — it does not affect the test results.

---

## 11. Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"

The virtual environment is not activated, or dependencies are not installed:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

### "WARNING: The following environment variables are NOT set in .env"

You have not filled in your real IBM credentials. Open `.env` and replace the placeholder text. Then run the connection test:

```powershell
python -m services.granite_service --test
```

### "Authentication error" / BXNIM0415E

Your API key is wrong or expired. Generate a new key on https://cloud.ibm.com/iam/apikeys and update `.env`.

### "MissingFoundationModel" error

The model ID in your `.env` is not available in your region. List what is available:

```powershell
python -m services.granite_service --list-models
```

For the Frankfurt region (`eu-de`) use `ibm/granite-3-1-8b-base`.

### Questions are not generated — app redirects back to setup

Check the terminal running `app.py` for the full error. Common causes: wrong project ID, model not enabled in your watsonx.ai project, or API quota reached.

### "Address already in use" on port 5000

Another process is using port 5000 (common on macOS where AirPlay uses 5000). Change the port in `app.py`:

```python
app.run(debug=Config.DEBUG, port=5001)
```

Then open http://localhost:5001.

### The database file is deleted / lost

`init_db()` runs every time the app starts. It re-creates missing tables automatically. Existing data in a surviving `.db` file is preserved.

---

## 12. CLI Utilities

These commands are useful for debugging and demonstration:

```powershell
# Test that IBM Granite is reachable with your credentials
python -m services.granite_service --test

# List all AI models available in your region
python -m services.granite_service --list-models

# See exactly what the RAG retriever picks for a given role/type/difficulty
python -m services.rag_service --report "Python Developer" Technical Intermediate
python -m services.rag_service --report "Data Analyst" HR Advanced
```

---

*Built by a B.Tech Information Technology student for a college demonstration.*
*All IBM watsonx.ai calls use real API credentials — no hardcoded or fake AI responses.*
