# InterviewMate AI – Project Plan

## Top-Level Overview

Build a complete Flask web application called **InterviewMate AI** that uses IBM watsonx.ai (IBM Granite model) to conduct mock interviews, evaluate answers, and display a personal dashboard. The project is designed as a college demonstration suitable for a beginner B.Tech IT student.

**Stack:** Python 3, Flask, SQLite, IBM watsonx-ai SDK, HTML/CSS/JS (vanilla), python-dotenv  
**Credential strategy:** `.env` file loaded via `python-dotenv` — credentials never appear in source code  
**RAG strategy:** Lightweight file-based knowledge base (JSON files per role) — no vector database required  
**Scope:** Single-user local web app; no authentication/login system required for the demo

---

## Architecture

```
Browser  <-->  Flask Routes  <-->  AI Service (watsonx)
                    |
              SQLite Database
                    |
           Knowledge Base (JSON files)
```

### Request flow for an interview session
1. User fills the setup form (role, type, difficulty, question count).
2. Flask asks IBM Granite to generate N questions using RAG context from the JSON knowledge base.
3. Questions are saved to SQLite; the interview page renders them one by one.
4. User submits all answers; Flask sends each answer to IBM Granite for evaluation.
5. Scores + feedback are saved to SQLite and displayed on a results page.
6. Dashboard reads aggregated stats from SQLite.

---

## Folder Structure

```
InterviewMate-AI/
├── app.py                     # Flask application entry point
├── config.py                  # App configuration (loads .env)
├── .env                       # IBM watsonx credentials (NOT committed to git)
├── .env.example               # Template showing required keys
├── .gitignore
├── requirements.txt
├── README.md
│
├── database/
│   ├── db.py                  # SQLite connection helper + schema init
│   └── interviewmate.db       # Auto-created on first run
│
├── services/
│   ├── ai_service.py          # All IBM watsonx.ai calls (generate + evaluate)
│   └── rag_service.py         # Loads knowledge base JSON, builds prompt context
│
├── knowledge_base/
│   ├── java_developer.json
│   ├── python_developer.json
│   ├── web_developer.json
│   ├── data_analyst.json
│   └── software_engineer.json
│
├── routes/
│   ├── __init__.py
│   ├── interview.py           # /setup, /generate, /submit, /results/<id>
│   └── dashboard.py           # /dashboard, /history
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── interview.js       # Timer, progress bar, answer collection
│
└── templates/
    ├── base.html              # Shared layout with navbar
    ├── index.html             # Landing / home page
    ├── setup.html             # Interview configuration form
    ├── interview.html         # Question-answer interface
    ├── results.html           # Per-session feedback page
    └── dashboard.html         # Stats + history table
```

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffolding & Configuration

**Intent:** Create the skeleton files, dependency list, `.env` template, `.gitignore`, and database schema. Everything else depends on this being in place first.

**Expected Outcomes:**
- `requirements.txt` lists all dependencies.
- `.env.example` documents the three required IBM keys.
- `config.py` loads `.env` safely.
- `database/db.py` can create the SQLite schema on first run.
- `app.py` starts Flask without errors (even before routes are wired).

**Todo List:**
1. Create `requirements.txt` with: flask, python-dotenv, ibm-watsonx-ai, and requests.
2. Create `.env.example` with keys: `IBM_WATSONX_API_KEY`, `IBM_WATSONX_PROJECT_ID`, `IBM_WATSONX_URL`.
3. Create `.env` (copy of `.env.example` with placeholder values — user fills in real values).
4. Create `.gitignore` excluding `.env`, `*.db`, `__pycache__`, `.venv`.
5. Create `config.py` that reads `.env` via `python-dotenv` and exposes a `Config` class.
6. Create `database/db.py` with:
   - `get_db()` — returns a SQLite connection.
   - `init_db()` — runs the CREATE TABLE statements.
   - Schema: `sessions` table and `questions` table (see Sub-Task 5 for column details).
7. Create minimal `app.py` that creates the Flask app, calls `init_db()`, and runs on port 5000.

**Relevant Context:** No existing files. Start from scratch.

**Status:** [ ] pending

---

### Sub-Task 2 — Knowledge Base (RAG Data)

**Intent:** Populate five JSON knowledge-base files — one per job role — with sample interview questions and key concepts. The AI service reads these at question-generation time to provide role-specific context to IBM Granite, implementing a lightweight RAG pattern.

**Expected Outcomes:**
- Five JSON files exist under `knowledge_base/`.
- Each file has keys: `role`, `technical_topics`, `hr_topics`, `sample_questions` (10–15 per difficulty level).
- `services/rag_service.py` can load a file by role name and return a formatted context string.

**Todo List:**
1. Create `knowledge_base/java_developer.json` with Java-specific topics and sample questions.
2. Create `knowledge_base/python_developer.json`.
3. Create `knowledge_base/web_developer.json`.
4. Create `knowledge_base/data_analyst.json`.
5. Create `knowledge_base/software_engineer.json`.
6. Create `services/rag_service.py` with function `get_context(role, interview_type, difficulty)` that returns a formatted string of relevant topics and sample questions for use in prompts.

**Relevant Context:** Role names used in the UI: "Java Developer", "Python Developer", "Web Developer", "Data Analyst", "Software Engineer". These must match the JSON file naming convention (lowercase + underscore).

**Status:** [ ] pending

---

### Sub-Task 3 — AI Service (IBM watsonx.ai Integration)

**Intent:** Implement the two IBM Granite API calls: (1) generate interview questions, and (2) evaluate a single answer. These functions are the core intelligence of the app.

**Expected Outcomes:**
- `services/ai_service.py` exposes two functions:
  - `generate_questions(role, interview_type, difficulty, count, rag_context)` → returns a Python list of question strings.
  - `evaluate_answer(question, answer, role)` → returns a dict with keys: `score`, `correctness`, `clarity`, `completeness`, `strengths`, `improvements`, `sample_answer`.
- Both functions handle API errors gracefully and return fallback values on failure.
- Responsible AI disclaimer text is defined as a module-level constant.

**Todo List:**
1. Import `WatsonxLLM` (or the `ModelInference` class) from `ibm_watsonx_ai` and load credentials from `config.Config`.
2. Write `generate_questions()`:
   - Build a prompt that includes the RAG context, role, type, difficulty, and requested count.
   - Call IBM Granite (`ibm/granite-13b-instruct-v2` or `ibm/granite-3-8b-instruct`).
   - Parse the plain-text response into a Python list (split on numbered lines).
   - Return the list.
3. Write `evaluate_answer()`:
   - Build a structured prompt asking IBM Granite to rate the answer on score/correctness/clarity/completeness/strengths/improvements/sample_answer.
   - Parse the response into a Python dict.
   - Return the dict.
4. Add `RESPONSIBLE_AI_NOTICE` constant: "Scores are AI estimates for practice only and are not hiring decisions. Your data is used solely for session feedback."
5. Add try/except around all API calls; return safe defaults on error.

**Relevant Context:** IBM watsonx.ai Python SDK — `ibm_watsonx_ai.foundation_models.ModelInference`. Credentials come from `config.Config`. RAG context string comes from `rag_service.get_context()`.

**Status:** [ ] pending

---

### Sub-Task 4 — Flask Routes

**Intent:** Wire up all URL endpoints so the browser can navigate through the full interview flow: home → setup → interview → results → dashboard.

**Expected Outcomes:**
- `GET /` → renders `index.html`.
- `GET /setup` → renders `setup.html` (the configuration form).
- `POST /generate` → calls AI service, saves session + questions to DB, redirects to `/interview/<session_id>`.
- `GET /interview/<session_id>` → renders `interview.html` with questions.
- `POST /submit/<session_id>` → evaluates all answers, saves feedback, redirects to `/results/<session_id>`.
- `GET /results/<session_id>` → renders `results.html`.
- `GET /dashboard` → renders `dashboard.html` with stats.

**Todo List:**
1. Create `routes/__init__.py` (empty).
2. Create `routes/interview.py` with blueprints for `/`, `/setup`, `/generate`, `/interview/<id>`, `/submit/<id>`, `/results/<id>`.
3. Create `routes/dashboard.py` with blueprint for `/dashboard`.
4. Register both blueprints in `app.py`.
5. Each route must read/write the DB via `database/db.py` helper functions.
6. `/generate` must call `rag_service.get_context()` then `ai_service.generate_questions()`.
7. `/submit/<id>` must loop over submitted answers, call `ai_service.evaluate_answer()` for each, and store scores.

**Relevant Context:** Use Flask Blueprints. Session ID is the `rowid` of the `sessions` table.

**Status:** [ ] pending

---

### Sub-Task 5 — Database Schema & Helper Functions

**Intent:** Define the SQLite tables and add helper functions so routes can store and retrieve data without writing raw SQL in every route.

**Expected Outcomes:**
- Two tables: `sessions` and `questions`.
- Helper functions: `create_session()`, `save_questions()`, `save_answer()`, `get_session()`, `get_questions()`, `get_dashboard_stats()`, `get_history()`.

**Todo List:**
1. Define `sessions` table columns:
   - `id` INTEGER PRIMARY KEY AUTOINCREMENT
   - `role` TEXT, `interview_type` TEXT, `difficulty` TEXT
   - `total_questions` INTEGER, `average_score` REAL
   - `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   - `completed` INTEGER DEFAULT 0
2. Define `questions` table columns:
   - `id` INTEGER PRIMARY KEY AUTOINCREMENT
   - `session_id` INTEGER (FK → sessions.id)
   - `question_text` TEXT
   - `answer_text` TEXT
   - `score` REAL, `correctness` TEXT, `clarity` TEXT, `completeness` TEXT
   - `strengths` TEXT, `improvements` TEXT, `sample_answer` TEXT
3. Add all helper functions to `database/db.py`.
4. `get_dashboard_stats()` returns: total_sessions, total_answers, avg_score (computed with SQL AVG).

**Relevant Context:** `database/db.py` is created in Sub-Task 1 with stubs. This sub-task fills in the actual SQL.

**Status:** [ ] pending

---

### Sub-Task 6 — HTML Templates & CSS

**Intent:** Build the complete user interface — all six templates sharing one base layout, plus a stylesheet that looks professional for a college demo.

**Expected Outcomes:**
- `templates/base.html` — navbar with logo, links to Home, New Interview, Dashboard; footer with responsible AI notice.
- `templates/index.html` — landing page with hero section, feature cards, "Start Interview" button.
- `templates/setup.html` — form with four dropdowns (role, type, difficulty, count) and a submit button.
- `templates/interview.html` — shows each question with a textarea; progress indicator; submit all button.
- `templates/results.html` — accordion cards per question showing score badge, feedback fields, sample answer.
- `templates/dashboard.html` — stat cards (total sessions, total answers, avg score) and history table.
- `static/css/style.css` — consistent colour scheme, responsive layout, card styles.

**Todo List:**
1. Create `templates/base.html` with block structure (title, content, scripts).
2. Create `templates/index.html`.
3. Create `templates/setup.html` with form posting to `/generate`.
4. Create `templates/interview.html` with dynamic question rendering and a form posting to `/submit/<session_id>`.
5. Create `templates/results.html` showing per-question feedback from the DB.
6. Create `templates/dashboard.html`.
7. Create `static/css/style.css` with IBM-inspired blue/grey palette, card layout, responsive grid.

**Relevant Context:** Use Jinja2 templating (Flask default). No external CSS framework — vanilla CSS only (keeps it beginner-friendly and dependency-free).

**Status:** [ ] pending

---

### Sub-Task 7 — JavaScript (Interview Interaction)

**Intent:** Add minimal client-side JS to improve the interview experience: a timer, a progress indicator, and form validation before submission.

**Expected Outcomes:**
- `static/js/interview.js` shows a countdown timer (configurable minutes).
- A progress bar advances as the user fills in answers.
- A confirm dialog warns if the user tries to submit with empty answers.
- No external JS libraries required.

**Todo List:**
1. Create `static/js/interview.js`.
2. Implement `startTimer(minutes)` function that counts down and shows MM:SS.
3. Implement progress bar update on `input` events of all textareas.
4. Add form `submit` event listener that warns on empty answers.

**Relevant Context:** `templates/interview.html` loads this script. Timer duration: 30 minutes default (configurable via a `data-` attribute on the HTML element).

**Status:** [ ] pending

---

### Sub-Task 8 — README & Setup Instructions

**Intent:** Write clear, beginner-friendly setup instructions so the student can run the project on any machine and demonstrate it confidently.

**Expected Outcomes:**
- `README.md` covers: prerequisites, installation steps, `.env` configuration, how to run, how to use, project structure, responsible AI notice.
- Instructions are numbered and copy-pasteable.

**Todo List:**
1. Write `README.md` with all sections listed above.
2. Include the exact pip install command from `requirements.txt`.
3. Explain where to get IBM watsonx.ai API keys (IBM Cloud → watsonx.ai project).
4. Add a "Responsible AI" section matching the in-app notice.

**Relevant Context:** Target reader is a beginner B.Tech student who may never have used Flask or IBM Cloud before.

**Status:** [ ] pending

---

## Testing Plan

| What to test | How |
|---|---|
| App starts without errors | Run `python app.py`, visit `http://localhost:5000` |
| Setup form submits correctly | Fill all dropdowns, click Generate — check redirects to interview page |
| Questions are generated | Verify questions appear on the interview page |
| Answer submission works | Submit answers — check results page shows scores and feedback |
| Dashboard shows correct stats | Complete 2–3 sessions, check counts and average match |
| DB persistence | Restart the app, re-visit dashboard — history should still be there |
| API error handling | Use a wrong API key in `.env` — app should show a friendly error, not crash |
| Responsible AI notice | Check footer and results page display the disclaimer |

---

## Responsible AI Notices

The following text must appear in the app footer and on the results page:

> "AI-generated scores are estimates for practice purposes only and do not represent actual hiring decisions. Your answers are processed by IBM watsonx.ai and are not stored beyond your session. API credentials are stored locally in your `.env` file and are never transmitted to third parties."

---

## IBM watsonx.ai Quick Reference

- **Model ID to use:** `ibm/granite-3-8b-instruct` (lightweight, good instruction-following)
- **SDK class:** `ibm_watsonx_ai.foundation_models.ModelInference`
- **Required `.env` keys:**
  - `IBM_WATSONX_API_KEY` — from IBM Cloud IAM
  - `IBM_WATSONX_PROJECT_ID` — from your watsonx.ai project
  - `IBM_WATSONX_URL` — e.g. `https://us-south.ml.cloud.ibm.com`
