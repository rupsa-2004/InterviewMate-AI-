# InterviewMate AI – System Architecture & Technical Design

> Full technical documentation for the college project submission.
> All diagrams use plain-text ASCII / Mermaid format for portability.

---

## Table of Contents

1. [System Architecture Diagram](#1-system-architecture-diagram)
2. [Data Flow Diagram](#2-data-flow-diagram)
3. [Database Schema](#3-database-schema)
4. [Technology Stack](#4-technology-stack)
5. [IBM Granite and watsonx.ai Integration](#5-ibm-granite-and-watsonxai-integration)
6. [RAG Implementation](#6-rag-implementation)
7. [Responsible AI and Security](#7-responsible-ai-and-security)

---

## 1. System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Student's Computer                            │
│                                                                      │
│  ┌──────────────┐    HTTP     ┌───────────────────────────────────┐  │
│  │   Browser    │ ◄─────────► │        Flask Web Server           │  │
│  │  (HTML/CSS/  │             │         (app.py  port 5000)       │  │
│  │    JS)       │             │                                   │  │
│  └──────────────┘             │  ┌────────────┐  ┌─────────────┐ │  │
│                               │  │  routes/   │  │  routes/    │ │  │
│                               │  │interview.py│  │dashboard.py │ │  │
│                               │  └─────┬──────┘  └──────┬──────┘ │  │
│                               │        │                 │        │  │
│                               │  ┌─────▼─────────────────▼─────┐ │  │
│                               │  │         services/            │ │  │
│                               │  │  ┌────────────────────────┐  │ │  │
│                               │  │  │  granite_service.py    │  │ │  │
│                               │  │  │  (IBM Granite SDK)     │  │ │  │
│                               │  │  └──────────┬─────────────┘  │ │  │
│                               │  │             │                 │ │  │
│                               │  │  ┌──────────▼─────────────┐  │ │  │
│                               │  │  │   rag_service.py        │  │ │  │
│                               │  │  │  (Keyword retrieval)   │  │ │  │
│                               │  │  └────────────────────────┘  │ │  │
│                               │  └──────────────────────────────┘ │  │
│                               │                                   │  │
│                               │  ┌────────────────────────────┐  │  │
│                               │  │      database/db.py        │  │  │
│                               │  │   (SQLite via stdlib)      │  │  │
│                               │  └────────────────────────────┘  │  │
│                               └───────────────────────────────────┘  │
│                                         │           │                 │
│                           ┌─────────────┘           └──────────────┐ │
│                           ▼                                         ▼ │
│              ┌────────────────────────┐       ┌────────────────────┐ │
│              │  knowledge_base/*.json │       │  interviewmate.db  │ │
│              │  (5 role JSON files)   │       │  (SQLite file)     │ │
│              └────────────────────────┘       └────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                            HTTPS  │  IBM watsonx.ai SDK
                                   ▼
              ┌────────────────────────────────────────┐
              │          IBM Cloud (Frankfurt)          │
              │  eu-de.ml.cloud.ibm.com                │
              │                                        │
              │  ┌──────────────────────────────────┐  │
              │  │  IBM IAM  (token exchange)        │  │
              │  └──────────────────────────────────┘  │
              │                                        │
              │  ┌──────────────────────────────────┐  │
              │  │  ibm/granite-3-1-8b-base          │  │
              │  │  Foundation Model                 │  │
              │  │  (text generation endpoint)       │  │
              │  └──────────────────────────────────┘  │
              └────────────────────────────────────────┘
```

### Component Responsibilities

| Component | File | Responsibility |
|-----------|------|---------------|
| Flask App | `app.py` | Creates app, registers blueprints, calls `init_db()` |
| Config | `config.py` | Reads `.env`, validates credentials, detects placeholders |
| Interview Routes | `routes/interview.py` | 6 endpoints: index, setup, generate, interview, submit, results |
| Dashboard Route | `routes/dashboard.py` | 1 endpoint: dashboard stats + history |
| Granite Service | `services/granite_service.py` | IBM SDK wrapper, prompt construction, response parsing, error mapping |
| RAG Service | `services/rag_service.py` | Knowledge-base loading, keyword scoring, context assembly |
| DB Helpers | `database/db.py` | Schema init, migration, 8 CRUD helpers |
| Knowledge Base | `knowledge_base/*.json` | Static domain knowledge per role |
| SQLite DB | `database/interviewmate.db` | Persistent session, question, answer, score storage |
| Templates | `templates/*.html` | Jinja2 HTML — 6 pages sharing a base layout |
| Style | `static/css/style.css` | Full design system: purple `#6c63ff` + white palette |
| JS | `static/js/interview.js` | Timer, progress bar, unsaved-changes warning |

---

## 2. Data Flow Diagram

### Flow A: Generating Interview Questions

```
Student                 Flask              RAG Service          IBM Granite
  │                       │                    │                    │
  │  POST /generate        │                    │                    │
  │  (role, type,          │                    │                    │
  │   difficulty, count)   │                    │                    │
  ├──────────────────────►│                    │                    │
  │                        │  retrieve(role,    │                    │
  │                        │   type, diff)      │                    │
  │                        ├───────────────────►│                    │
  │                        │                    │ 1. Load JSON KB    │
  │                        │                    │ 2. Tokenize query  │
  │                        │                    │ 3. Score all items │
  │                        │                    │ 4. Return top-N    │
  │                        │  context_str       │                    │
  │                        │◄───────────────────┤                    │
  │                        │                    │                    │
  │                        │  generate_questions(role, type,        │
  │                        │   diff, count, context_str)            │
  │                        ├────────────────────────────────────────►
  │                        │                    │  Structured prompt │
  │                        │                    │  with RAG context  │
  │                        │                    │◄──── questions ────┤
  │                        │  parse numbered    │                    │
  │                        │  list → [str]      │                    │
  │                        │                    │                    │
  │                        │ create_session()                        │
  │                        │ save_questions()   │                    │
  │                        │  [SQLite]          │                    │
  │                        │                    │                    │
  │  302 → /interview/<id> │                    │                    │
  │◄──────────────────────┤                    │                    │
```

### Flow B: Evaluating Answers

```
Student                 Flask              RAG Service          IBM Granite
  │                       │                    │                    │
  │  POST /submit/<id>     │                    │                    │
  │  (answer_1, answer_2,  │                    │                    │
  │   answer_3, ...)       │                    │                    │
  ├──────────────────────►│                    │                    │
  │                        │  For each question:│                    │
  │                        │  get_evaluation_context(role, q_text)  │
  │                        ├───────────────────►│                    │
  │                        │  domain context    │                    │
  │                        │◄───────────────────┤                    │
  │                        │                    │                    │
  │                        │  evaluate_answer(q, answer,            │
  │                        │   role, domain_context)                │
  │                        ├────────────────────────────────────────►
  │                        │                    │  Structured eval   │
  │                        │                    │  prompt with       │
  │                        │                    │  domain context    │
  │                        │                    │◄── SCORE/FIELDS ───┤
  │                        │  _parse_evaluation()                    │
  │                        │  → {score, correctness, clarity, ...}  │
  │                        │  save_answer() [SQLite]                 │
  │                        │                    │                    │
  │                        │  complete_session() [SQLite]            │
  │                        │  (sets completed=1, avg_score=AVG)     │
  │                        │                    │                    │
  │  302 → /results/<id>   │                    │                    │
  │◄──────────────────────┤                    │                    │
```

### Flow C: Dashboard

```
Student                 Flask              SQLite
  │                       │                   │
  │  GET /dashboard        │                   │
  ├──────────────────────►│                   │
  │                        │ get_dashboard_stats()
  │                        ├──────────────────►│
  │                        │ {total_sessions,  │
  │                        │  total_answers,   │
  │                        │  avg_score,       │
  │                        │  by_role}         │
  │                        │◄──────────────────┤
  │                        │ get_history()     │
  │                        ├──────────────────►│
  │                        │ [session rows]    │
  │                        │◄──────────────────┤
  │  200 dashboard.html    │                   │
  │◄──────────────────────┤                   │
```

---

## 3. Database Schema

The SQLite database has **two tables**: `sessions` and `questions`.
The database file is created automatically at `database/interviewmate.db` on first run.

### `sessions` table

Stores one row per interview session.

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id              INTEGER  PRIMARY KEY AUTOINCREMENT,
    student_name    TEXT     NOT NULL DEFAULT '',
    role            TEXT     NOT NULL,
    interview_type  TEXT     NOT NULL,
    difficulty      TEXT     NOT NULL,
    total_questions INTEGER  NOT NULL DEFAULT 0,
    average_score   REAL     DEFAULT 0.0,
    completed       INTEGER  DEFAULT 0,        -- 0 = in progress, 1 = completed
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Auto-incrementing primary key |
| `student_name` | TEXT | Optional name entered at setup; empty string if not given |
| `role` | TEXT | One of the 5 supported job roles |
| `interview_type` | TEXT | Technical, HR, or Mixed |
| `difficulty` | TEXT | Beginner, Intermediate, or Advanced |
| `total_questions` | INTEGER | How many questions were generated |
| `average_score` | REAL | Computed by `complete_session()` as `ROUND(AVG(score), 1)` |
| `completed` | INTEGER | 0 while the user is answering; set to 1 after all evaluations |
| `created_at` | TIMESTAMP | Auto-set by SQLite on INSERT |

### `questions` table

Stores one row per question, with the student's answer and all AI evaluation fields.

```sql
CREATE TABLE IF NOT EXISTS questions (
    id              INTEGER  PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER  NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_number INTEGER  NOT NULL DEFAULT 1,
    question_text   TEXT     NOT NULL,
    answer_text     TEXT     DEFAULT '',
    score           REAL     DEFAULT 0.0,
    correctness     TEXT     DEFAULT '',
    clarity         TEXT     DEFAULT '',
    completeness    TEXT     DEFAULT '',
    strengths       TEXT     DEFAULT '',
    improvements    TEXT     DEFAULT '',
    sample_answer   TEXT     DEFAULT '',
    evaluated       INTEGER  DEFAULT 0         -- 0 = not yet evaluated, 1 = done
);
```

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Auto-incrementing primary key |
| `session_id` | INTEGER | Foreign key to `sessions.id` (CASCADE delete) |
| `question_number` | INTEGER | 1-based position within the session |
| `question_text` | TEXT | The IBM Granite-generated question |
| `answer_text` | TEXT | The student's typed answer |
| `score` | REAL | AI-assigned score 0.0–10.0 |
| `correctness` | TEXT | AI feedback sentence on factual accuracy |
| `clarity` | TEXT | AI feedback sentence on how clearly the answer was expressed |
| `completeness` | TEXT | AI feedback sentence on coverage of key aspects |
| `strengths` | TEXT | AI feedback on what the student did well |
| `improvements` | TEXT | AI suggestions for improvement |
| `sample_answer` | TEXT | IBM Granite model answer (3–5 sentences) |
| `evaluated` | INTEGER | 0 = answer not yet evaluated; 1 = evaluation complete |

### Entity Relationship

```
sessions (1) ─────── (many) questions
  id  ◄────────────────── session_id
```

One session can have 3, 5, 7, or 10 questions.
If a session row is deleted, all its questions are deleted automatically (CASCADE).

### Safe Migration

`init_db()` calls `_migrate()` every startup. The migration checks for missing columns using `PRAGMA table_info(sessions)` and adds them with `ALTER TABLE` only if absent. This means:

- Existing databases from earlier project versions are upgraded automatically.
- No data is ever lost on a schema update.
- The `student_name` column (added after the initial schema) is handled this way.

### Key Queries

**Dashboard totals** (only completed sessions + evaluated answers):

```sql
SELECT
    COUNT(DISTINCT s.id)   AS total_sessions,
    COUNT(q.id)            AS total_answers,
    ROUND(AVG(q.score), 1) AS avg_score
FROM sessions s
INNER JOIN questions q ON q.session_id = s.id AND q.evaluated = 1
WHERE s.completed = 1;
```

**Per-role breakdown**:

```sql
SELECT s.role,
       COUNT(DISTINCT s.id)   AS sessions,
       ROUND(AVG(q.score), 1) AS avg_score
FROM sessions s
INNER JOIN questions q ON q.session_id = s.id AND q.evaluated = 1
WHERE s.completed = 1
GROUP BY s.role
ORDER BY sessions DESC;
```

---

## 4. Technology Stack

| Layer | Technology | Version | Why it was chosen |
|-------|-----------|---------|-------------------|
| **Language** | Python | 3.9+ | Required by the course; vast library ecosystem |
| **Web Framework** | Flask | ≥ 3.0.3 | Lightweight, beginner-friendly, standard choice for Python web apps |
| **Database** | SQLite (stdlib) | built-in | No external DB server needed; single file; sufficient for a college project |
| **ORM / DB Access** | `sqlite3` (stdlib) | built-in | Direct SQL is easy to understand and debug for students |
| **AI Foundation Model** | IBM Granite (`ibm/granite-3-1-8b-base`) | via watsonx.ai | Required by course; available in Frankfurt region; instruction-capable |
| **AI SDK** | `ibm-watsonx-ai` | ≥ 1.9.0 | Official IBM Python SDK for watsonx.ai `ModelInference` |
| **Credential management** | `python-dotenv` | ≥ 1.0.1 | Reads `.env` file into `os.environ`; keeps secrets out of source code |
| **HTTP** | `requests` | ≥ 2.32.3 | Transitive dependency of the IBM SDK |
| **Templating** | Jinja2 | (bundled with Flask) | Server-side HTML rendering; auto-escaping prevents XSS |
| **Frontend** | Vanilla HTML/CSS/JS | — | No framework dependency; works without npm or a build step |
| **RAG** | Custom keyword scorer | — | No external ML libraries; pure Python; transparent and debuggable |
| **Testing** | `unittest` + `unittest.mock` | stdlib | No extra install; mocks IBM SDK cleanly |

### Why no external ML libraries for RAG?

The course requires "lightweight RAG". The custom keyword scorer in [`services/rag_service.py`](../services/rag_service.py) achieves genuine retrieval:

1. Tokenises both the query and each knowledge-base item (lowercasing, stop-word removal).
2. Computes a **precision** score: fraction of query tokens found in the item.
3. Computes a **density** score: matches divided by the square root of item length, favouring shorter, denser matches.
4. Final score = `(precision + density) / 2`.
5. Sorts all items by score descending; returns top N.

This is behaviorally similar to BM25 but requires no `numpy`, no `sklearn`, and no vector index.

---

## 5. IBM Granite and watsonx.ai Integration

### How the IBM SDK is used

The project uses `ibm-watsonx-ai==1.9.0` with the `ModelInference` class:

```python
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

credentials = Credentials(
    url=Config.WATSONX_URL,
    api_key=Config.WATSONX_API_KEY,
)
model = ModelInference(
    model_id=Config.WATSONX_MODEL_ID,     # ibm/granite-3-1-8b-base
    credentials=credentials,
    project_id=Config.WATSONX_PROJECT_ID,
    params=generation_params,
    validate=True,                         # verifies model ID against the API
)
text = model.generate_text(prompt=prompt, params=params)
```

The `ModelInference` client is cached with `@lru_cache(maxsize=1)` so only one IAM token exchange happens per server process.

### Generation parameters

Two parameter sets are used depending on the task:

| Parameter | Question Generation | Answer Evaluation |
|-----------|--------------------|--------------------|
| `MAX_NEW_TOKENS` | 1024 | 1200 |
| `MIN_NEW_TOKENS` | 40 | 80 |
| `TEMPERATURE` | 0.7 (creative) | 0.3 (deterministic) |
| `TOP_P` | 0.9 | 0.85 |
| `REPETITION_PENALTY` | 1.1 | 1.05 |
| `STOP_SEQUENCES` | `["\n\n\n"]` | `["\n\n\n"]` |

Lower temperature for evaluation produces more consistent structured output that the parser can reliably extract.

### Prompt design: Question generation

```
You are an expert technical interviewer conducting a mock interview.

CONTEXT FROM KNOWLEDGE BASE:
<RAG context string — role, difficulty, topics, sample questions>

TASK:
Generate exactly {count} interview questions for a {difficulty}-level
{role} candidate. Interview type: {interview_type}.

RULES:
- Number each question starting from 1, like: 1. Question text here
- Each question must be on its own line.
- Do NOT include answers, hints, or explanations — only the questions.
- Make each question specific, clear, and appropriate for {difficulty} level.
- Do NOT repeat the instructions or context in your output.

QUESTIONS:
```

The numbered-list parser accepts several formats: `1.`, `1)`, `Q1:`, `Question 1:`, `1 -`.

### Prompt design: Answer evaluation

```
You are an expert interviewer evaluating a candidate's answer for a
{role} position.

KNOWLEDGE BASE CONTEXT:
<domain context from RAG>

QUESTION:
{question}

CANDIDATE'S ANSWER:
{answer}

Evaluate the answer and respond in EXACTLY this format.
Use the field names exactly as shown. Do not add any text outside these fields.

SCORE: [a single number from 0 to 10]
CORRECTNESS: [one or two sentences: is the answer technically correct?]
CLARITY: [one or two sentences: is it well-explained and easy to follow?]
COMPLETENESS: [one or two sentences: does it cover all key aspects?]
STRENGTHS: [one or two sentences: what did the candidate do well?]
IMPROVEMENTS: [one or two sentences: what should they add or correct?]
SAMPLE_ANSWER: [3–5 sentences: a model answer for this question]
```

The response parser uses `re.DOTALL` with `\Z` (absolute end-of-string) lookahead so multi-line fields and the last field (`SAMPLE_ANSWER`) are captured reliably.

### Error handling

Every IBM SDK exception is mapped to one of two project-level exceptions:

| SDK Exception | Project Exception | Meaning |
|--------------|-------------------|---------|
| `AuthenticationError` | `GraniteAuthError` | Wrong API key or expired token |
| `InvalidCredentialsError` | `GraniteAuthError` | Credentials rejected by IBM IAM |
| `NoWMLCredentialsProvided` | `GraniteAuthError` | Missing credentials |
| `MissingFoundationModel` | `GraniteAPIError` | Model ID not available in region |
| `ExceededLimitOfAPICalls` | `GraniteAPIError` | API quota reached |
| `ApiRequestFailure` | `GraniteAPIError` | HTTP error from the IBM endpoint |
| `WMLClientError` (other) | `GraniteAPIError` | Network error, timeout, etc. |
| Empty response (`""`) | `GraniteAPIError` | Model generated no text |

Routes catch `GraniteAuthError` and `GraniteAPIError` separately. Auth errors abort the session immediately (because all remaining calls will also fail). Non-auth errors on individual questions are logged and the session continues with a zero-score placeholder, so the student is not blocked from seeing the rest of their results.

### Security

- Credentials are read only from `Config` (which reads from `.env`).
- They are never printed to logs, HTML, or JavaScript.
- The `Config.validate()` method detects not just empty strings but also common placeholder strings (e.g. `"your_ibm_cloud_api_key_here"`) using substring matching against a list of known patterns.
- The `.env` file is in `.gitignore`.

---

## 6. RAG Implementation

RAG stands for **Retrieval-Augmented Generation**. Instead of asking IBM Granite to generate questions from scratch with no context, the system first *retrieves* relevant material from a local knowledge base and injects it into the prompt. This makes questions more targeted and evaluation more grounded.

### Knowledge base structure

Each of the 5 job roles has a JSON file (`knowledge_base/<role>.json`) with this structure:

```json
{
  "role": "Python Developer",
  "technical_topics": [
    "Python data types and mutability: lists, tuples, sets, dictionaries",
    "OOP in Python: classes, inheritance, polymorphism, dunder methods",
    "Decorators, closures, and higher-order functions",
    ...
  ],
  "hr_topics": [
    "Communication: explaining technical concepts to non-technical stakeholders",
    "Teamwork and collaboration in Agile/Scrum environments",
    ...
  ],
  "sample_questions": {
    "beginner": [
      "What is the difference between a list and a tuple in Python?",
      ...
    ],
    "intermediate": [ ... ],
    "advanced": [ ... ]
  }
}
```

Each file contains approximately 15 technical topics, 8 HR topics, and 10–15 sample questions per difficulty level.

### Retrieval algorithm (step by step)

Given: role = "Python Developer", interview_type = "Technical", difficulty = "Intermediate"

**Step 1 – Role routing**

The role name maps to a JSON filename:
- `"Python Developer"` → `knowledge_base/python_developer.json`

**Step 2 – Pool selection**

The interview type selects which topic pools to search:
- `"Technical"` → search `technical_topics` only
- `"HR"` → search `hr_topics` only
- `"Mixed"` → search both pools

**Step 3 – Query construction**

A query string is built: `"Python Developer Technical Intermediate interview questions"`

This is tokenised (lowercased, stop-words removed) to produce: `["python", "developer", "technical", "intermediate", "interview", "questions"]`

**Step 4 – Scoring**

Every item in the selected pool is scored against the query tokens:

```
score(item) = (precision + density) / 2

precision = (matching tokens) / (total query tokens)
density   = (matching tokens) / sqrt(len(item tokens))
```

Example: item = `"Python asyncio, event loops, coroutines, async/await patterns"`
- Item tokens: `{python, asyncio, event, loops, coroutines, async, await, patterns}`
- Query tokens: `{python, developer, technical, intermediate, interview, questions}`
- Matches: `python` → 1 match
- precision = 1/6 ≈ 0.167
- density = 1/√8 ≈ 0.354
- score ≈ 0.26

Items with higher overlap with the query are ranked first.

**Step 5 – Sample question retrieval**

Sample questions for the exact difficulty are loaded. If none exist (unlikely), the adjacent difficulty is used as a fallback.

**Step 6 – Context assembly**

Retrieved topics and samples are formatted into a structured context string:

```
ROLE: Python Developer
INTERVIEW TYPE: Technical
DIFFICULTY: Intermediate

RELEVANT TOPICS FROM KNOWLEDGE BASE:
  - Python data types and mutability: lists, tuples, sets, dictionaries
  - OOP in Python: classes, inheritance, polymorphism, dunder methods
  - ...

SAMPLE REFERENCE QUESTIONS (Intermediate level):
  - Explain Python's memory management and garbage collection.
  - What is the difference between deep copy and shallow copy?
  - ...

Use the above retrieved knowledge to generate FRESH, UNIQUE questions
for the specified role, type, and difficulty.
```

This full string is injected verbatim into the IBM Granite prompt.

### Verifying retrieval

You can inspect exactly what is retrieved using the CLI tool:

```powershell
python -m services.rag_service --report "Python Developer" Technical Intermediate
```

This proves that retrieval is happening at query time (not a fixed list slice).

### What makes this RAG (not just prompting)?

| Property | This implementation |
|----------|-------------------|
| **Retrieval** | Yes — scores and ranks items from a corpus at query time |
| **Augmentation** | Yes — retrieved items are injected into the prompt |
| **Generation** | Yes — IBM Granite generates from the augmented prompt |
| **Dynamic** | Yes — different role/type/difficulty → different retrieved content |
| **Lightweight** | Yes — no vector DB, no embeddings, pure Python |

---

## 7. Responsible AI and Security

### Responsible AI principles applied

**1. Transparency**

- The AI notice is displayed on both the interview page and the results page.
- The exact text: *"AI-generated scores are estimates for practice purposes only and do not represent actual hiring decisions."*
- The source model (`IBM Granite`) is named in the notice.

**2. No fake results**

- If IBM Granite is unavailable or credentials are wrong, the application raises a real exception and shows an error — it never substitutes hardcoded scores or fake feedback.
- This ensures students always know whether they are seeing real AI evaluation or an error.

**3. Purpose limitation**

- The system is explicitly described as a practice tool, not a hiring tool.
- No data is shared with any third party beyond the IBM watsonx.ai API call.

**4. Score as estimate**

- The score (0–10) is clamped to valid range but never presented as a definitive assessment.
- All evaluation dimensions (correctness, clarity, etc.) are AI-generated estimates.

### Security measures

| Threat | Mitigation |
|--------|-----------|
| **Credential exposure** | `.env` is in `.gitignore`; credentials never appear in HTML, JS, or logs |
| **Placeholder credentials** | `Config.validate()` detects and warns on 13 known placeholder substrings |
| **XSS via student name** | `{{ s.student_name \| e }}` escapes HTML entities in Jinja2 templates |
| **SQL injection** | All queries use parameterised SQLite placeholders (`?`) — no string formatting in SQL |
| **Session ID tampering** | Results and interview pages return 404 / redirect for unknown session IDs |
| **CSRF** | Flask's secret key is required for session cookies; production deployments should add Flask-WTF CSRF protection |
| **Model output injection** | AI text fields are rendered with Jinja2's default auto-escaping (no `\| safe` on AI content) |

### Privacy

- **No external data storage**: all interview sessions, answers, and scores are stored only in `database/interviewmate.db` on the student's own computer.
- **Minimal data**: only the fields needed for the interview (role, answers, scores) are stored. No personally identifying information is required (student name is optional).
- **No analytics**: the application makes no tracking or telemetry calls.
- **API calls only**: the only data leaving the machine is the question text and the student's answer, sent to IBM watsonx.ai for evaluation. IBM's data processing policies apply to this content.
