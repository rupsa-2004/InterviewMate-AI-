# InterviewMate AI – Testing Report

> **Project:** InterviewMate AI – Your Personal AI Interview Trainer
> **Date:** November 2026
> **Testing scope:** Automated tests only; no real IBM credentials required for the test suites.
> **Test runner:** Python standard library `unittest` / plain script with `sys.exit()`

---

## Summary

| Test Suite | File | Total Checks | Passed | Failed |
|------------|------|:---:|:---:|:---:|
| RAG + Database | `tests/test_rag_db.py` | 100 | **100** | 0 |
| Integration (Flask + mocked IBM SDK) | `tests/test_integration.py` | 75 | **75** | 0 |
| **Total** | | **175** | **175** | **0** |

Both suites exit with code `0` (success).

---

## How to Reproduce These Results

```powershell
# Activate the virtual environment
.venv\Scripts\activate

# Suite 1 — RAG + Database (no credentials needed)
python tests/test_rag_db.py

# Suite 2 — Integration (no credentials needed — IBM SDK is mocked)
python tests/test_integration.py
```

> **Note on stderr output during Suite 2:**
> The IBM SDK prints diagnostic messages to stderr when certain exception objects are constructed
> (e.g. `"Failed to retrieve Bearer token..."`, `"Exceeded limit of calls..."`).
> These are printed by the SDK's own `__init__` logging, not by the project code,
> and they appear even when the exceptions are successfully caught and suppressed by the tests.
> They do **not** indicate test failures. The exit code remains `0`.

---

## Suite 1: RAG + Database Tests (`tests/test_rag_db.py`)

**100 checks across 16 sections.**

### Section 1 — RAG: Knowledge Base Loading

Tests that all 5 role JSON files load correctly and contain the expected keys.

| Check | Result |
|-------|--------|
| KB loads for 'Java Developer' | PASS |
| KB loads for 'Python Developer' | PASS |
| KB loads for 'Web Developer' | PASS |
| KB loads for 'Data Analyst' | PASS |
| KB loads for 'Software Engineer' | PASS |
| Each role has `technical_topics` key | PASS (×5) |
| Each role has `hr_topics` key | PASS (×5) |
| Each role has `sample_questions` key | PASS (×5) |
| Each role has non-empty beginner samples | PASS (×5) |
| Each role has non-empty intermediate samples | PASS (×5) |
| Each role has non-empty advanced samples | PASS (×5) |

### Section 2 — RAG: Retrieval Scoring

Tests that different queries return different results (proving scoring is active, not a fixed slice).

| Check | Result |
|-------|--------|
| Technical retrieval returns topics | PASS |
| HR retrieval returns topics | PASS |
| Technical query returns ≥1 sample | PASS |
| HR query returns ≥1 sample | PASS |
| Java vs Web topics differ | PASS |
| Beginner vs Advanced samples differ | PASS |

### Section 3 — RAG: Context String

Tests that the assembled context string contains the retrieved items.

| Check | Result |
|-------|--------|
| Context string non-empty (>50 chars) | PASS |
| Context contains `ROLE:` header | PASS |
| Context contains `INTERVIEW TYPE:` header | PASS |
| Context contains `DIFFICULTY:` header | PASS |
| First retrieved topic appears in context | PASS |
| First retrieved sample appears in context | PASS |

### Section 4 — RAG: Evaluation Context

Tests that `get_evaluation_context()` returns role-specific topics for a given question.

| Check | Result |
|-------|--------|
| Evaluation context non-empty | PASS |
| Context mentions the role name | PASS |

### Section 5 — RAG: Retrieval Report

Tests the CLI diagnostic function.

| Check | Result |
|-------|--------|
| Report contains topic count | PASS |
| Report contains context section | PASS |
| Report lists role correctly | PASS |

### Section 6 — DB: Table Creation

| Check | Result |
|-------|--------|
| `sessions` table created by `init_db()` | PASS |
| `questions` table created by `init_db()` | PASS |

### Section 7 — DB: Migration

Tests that an old database (without `student_name`) is safely upgraded.

| Check | Result |
|-------|--------|
| `student_name` column added by migration | PASS |
| Existing rows preserved after migration | PASS |
| Existing `student_name` defaults to `''` | PASS |

### Section 8 — DB: Session Creation

| Check | Result |
|-------|--------|
| Session with `student_name` created | PASS |
| `student_name` stored correctly | PASS |
| `role`, `interview_type`, `difficulty` stored | PASS (×3) |
| `total_questions` stored correctly | PASS |
| `completed` starts at 0 | PASS |
| Session without `student_name` created | PASS |
| Empty `student_name` stored as `''` | PASS |

### Section 9 — DB: Questions Round-Trip

| Check | Result |
|-------|--------|
| 5 questions saved and retrieved | PASS |
| Questions ordered by `question_number` | PASS |
| First question text matches | PASS |
| All questions belong to correct session | PASS |
| All questions start as un-evaluated | PASS |

### Section 10 — DB: Answer Storage

| Check | Result |
|-------|--------|
| `answer_text` saved | PASS |
| `score` saved | PASS |
| `correctness` saved | PASS |
| `clarity` saved | PASS |
| `completeness` saved | PASS |
| `strengths` saved | PASS |
| `improvements` saved | PASS |
| `sample_answer` saved | PASS |
| `evaluated` flag set to 1 | PASS |

### Section 11 — DB: Session Completion

| Check | Result |
|-------|--------|
| `completed` set to 1 after `complete_session()` | PASS |
| `average_score` = 7.2 computed correctly (5 known scores) | PASS |

### Section 12 — DB: Persistence

Tests that data survives a simulated server restart (new SQLite connection).

| Check | Result |
|-------|--------|
| Session row survives DB reconnect | PASS |
| `student_name` persists | PASS |
| `completed=1` persists | PASS |
| `average_score` persists | PASS |
| All 5 question rows persist | PASS |
| Answer text persists across reconnect | PASS |

### Section 13 — DB: Dashboard Statistics

| Check | Result |
|-------|--------|
| `total_sessions` counts only completed sessions | PASS |
| `total_answers` counts only evaluated answers | PASS |
| `avg_score` is a number | PASS |
| `by_role` is a list | PASS |
| `by_role` contains 'Python Developer' entry | PASS |
| Incomplete session excluded from `total_sessions` | PASS |

### Section 14 — DB: History

| Check | Result |
|-------|--------|
| History is non-empty | PASS |
| History contains `student_name` field | PASS |
| History is newest-first | PASS |
| Incomplete session not in history | PASS |
| History row has all expected fields | PASS |

### Section 15 — DB: Session with Questions

| Check | Result |
|-------|--------|
| `get_session_with_questions()` returns dict | PASS |
| Result contains `questions` key | PASS |
| Embedded questions list has 5 items | PASS |
| Session fields (`role`, `student_name`) present | PASS |
| Returns `None` for unknown session ID | PASS |

### Section 16 — Integration: Full Session Flow

End-to-end simulation of a complete interview session using real DB and real RAG (no IBM API call).

| Check | Result |
|-------|--------|
| RAG retrieval returns non-empty context | PASS |
| RAG retrieved topics > 0 | PASS |
| RAG retrieved samples > 0 | PASS |
| 3 questions created in DB | PASS |
| Evaluation context non-empty for Q1, Q2, Q3 | PASS (×3) |
| Session completed with `completed=1` | PASS |
| `average_score=6.0` computed correctly | PASS |
| Dashboard `total_sessions` ≥ 2 | PASS |
| `by_role` contains 'Web Developer' | PASS |
| Both sessions appear in history | PASS |
| History IDs are integers | PASS |

---

## Suite 2: Integration Tests (`tests/test_integration.py`)

**75 checks across 12 areas.**
IBM API calls are intercepted with `unittest.mock.patch` — no real credentials are needed.

### Area 1 — Config Placeholder Detection

Tests that `Config.validate()` catches credentials that look like unfilled template values.

| Check | Result |
|-------|--------|
| `_is_placeholder('your_ibm_cloud_api_key_here')` = True | PASS |
| `_is_placeholder('your-ibm-api-key')` = True | PASS |
| `_is_placeholder('insert_your_key_here')` = True | PASS |
| `_is_placeholder('<your_project_id>')` = True | PASS |
| `_is_placeholder('api_key_here_fill_me')` = True | PASS |
| `_is_placeholder('project_id_here')` = True | PASS |
| `_is_placeholder('xxxxxxxxxxxxxxxxxxxxxxxxx')` = True | PASS |
| `_is_placeholder('changeme')` = True | PASS |
| Empty string → `_is_placeholder` = False | PASS |
| `_is_placeholder('abc123realkey456xyz')` = False | PASS |
| `_is_placeholder('7a9b2c3d-1234-5678-...')` = False | PASS |
| `_is_placeholder('https://eu-de.ml.cloud.ibm.com')` = False | PASS |
| `validate()` reports `WATSONX_API_KEY` when placeholder | PASS |

### Area 2 — Config Real Values

| Check | Result |
|-------|--------|
| No missing vars when all fields are real values | PASS |
| Empty `WATSONX_URL` is caught by `validate()` | PASS |

### Area 3 — `_parse_evaluation` Regex Coverage

Tests the structured output parser for all edge cases.

| Check | Result |
|-------|--------|
| Score parsed from clean output | PASS |
| Correctness, clarity, completeness, strengths, improvements, sample_answer all parsed | PASS (×6) |
| `sample_answer` captured without trailing newline (bug fix) | PASS |
| Score still parsed without trailing newline | PASS |
| Multi-line `sample_answer` captured across newlines | PASS |
| Score clamped to 10.0 when model returns 15 | PASS |
| Missing `SCORE` field raises `GraniteAPIError` | PASS |
| Numbered list parser handles formats: `1.`, `1)`, `Q1:`, `Q4:`, `Question 5:` | PASS |
| Numbered list first item text correct | PASS |

### Area 4 — Exception Hierarchy

Tests that every IBM SDK exception class is mapped to the correct project exception.

| Check | Result |
|-------|--------|
| `AuthenticationError` → `GraniteAuthError` | PASS |
| `ExceededLimitOfAPICalls` → `GraniteAPIError` | PASS |
| `WMLClientError` (generic) → `GraniteAPIError` | PASS |
| Empty response string → `GraniteAPIError` | PASS |
| `ApiRequestFailure` → `GraniteAPIError` | PASS |

### Area 5 — `generate_questions` (Mocked IBM SDK)

| Check | Result |
|-------|--------|
| Returns a list | PASS |
| Returns exactly 5 questions | PASS |
| No numbering prefix in returned strings | PASS |
| First question text matches mock response | PASS |
| All items are non-empty strings | PASS |
| Returns partial list when model gives fewer Qs | PASS |

### Area 6 — `evaluate_answer` (Mocked IBM SDK)

| Check | Result |
|-------|--------|
| All 7 required keys present (`score`, `correctness`, `clarity`, `completeness`, `strengths`, `improvements`, `sample_answer`) | PASS |
| Score value = 7.5 | PASS |
| Correctness, clarity, completeness, strengths, improvements all non-empty | PASS (×5) |
| Sample answer non-empty (>20 chars) | PASS |
| Score type is `float` | PASS |

### Area 7 — `GraniteAuthError` on Bad Credentials

| Check | Result |
|-------|--------|
| Empty credentials raise `GraniteAuthError` | PASS |
| Error message mentions `.env` file | PASS |
| Placeholder credentials raise `GraniteAuthError` | PASS |

### Area 8 — Flask Routes Reachable

| Check | Result |
|-------|--------|
| `GET /` → 200 | PASS |
| `GET /setup` → 200 | PASS |
| `GET /dashboard` → 200 | PASS |
| `POST /generate` (no form data) → 3xx (redirect back to setup) | PASS |
| `GET /this-does-not-exist` → 404 | PASS |

### Area 9 — `POST /generate` Session Creation

| Check | Result |
|-------|--------|
| `POST /generate` with valid form data → 302 | PASS |
| Redirects to `/interview/<id>` | PASS |
| Session row created in SQLite | PASS |
| `student_name = "Test Student"` stored | PASS |
| `role = "Python Developer"` stored | PASS |

### Area 10 — `POST /submit/<id>` Answer Evaluation

| Check | Result |
|-------|--------|
| Session ID retrieved from DB | PASS |
| Questions exist in DB for that session | PASS |
| `POST /submit/<id>` → 302 | PASS |
| Redirects to `/results/<id>` | PASS |
| Session `completed = 1` in DB | PASS |
| `average_score > 0` computed in DB | PASS |

### Area 11 — Results Page Rendering

| Check | Result |
|-------|--------|
| `GET /results/<id>` → 200 | PASS |
| Score ring SVG (`id="score-circle"`) present | PASS |
| Score number div (`id="score-number"`) present | PASS |
| Accordion header present | PASS |
| Accordion body present | PASS |
| AI responsible notice text present | PASS |
| Feedback grid present | PASS |
| Sample answer block present | PASS |
| Student name "Test Student" shown | PASS |
| `GET /results/99999` → 404 or redirect | PASS |

### Area 12 — Dashboard Page Rendering

| Check | Result |
|-------|--------|
| `GET /dashboard` → 200 | PASS |
| Stat card "Total Sessions" present | PASS |
| Stat card "Total Answers" present | PASS |
| Stat card "Average Score" present | PASS |
| History table (`data-table` class) rendered | PASS |
| "Python Developer" role appears in history | PASS |
| "Performance by Role" section rendered | PASS |
| "View Results" link present | PASS |
| Student name "Test Student" in history | PASS |
| XSS student name `<script>alert(1)</script>` is HTML-escaped | PASS |
| Escaped form `&lt;script&gt;` present (not raw tag) | PASS |

---

## What is NOT tested automatically

The following require real IBM Cloud credentials and are verified manually:

| Manual Test | How to verify |
|-------------|--------------|
| IBM Granite question generation | `python -m services.granite_service --test` |
| Full interview flow with real AI | Run `python app.py`, complete a session |
| Score ring animation | Visual inspection in browser |
| Timer countdown and auto-submit | Visual inspection; wait for timer |
| Mobile responsive layout | Resize browser or use DevTools device emulation |
| Navbar hamburger menu on mobile | DevTools mobile emulation |

---

## Bugs Found and Fixed During Testing

All bugs discovered during review were fixed before the final submission:

| # | Location | Bug | Fix |
|---|----------|-----|-----|
| 1 | `templates/results.html` | Dead code: `var bodyId = ... ? null : null;` in `toggleAccordion()` | Removed the unused variable |
| 2 | `config.py` | `validate()` only checked for empty strings; placeholder values like `"your_ibm_cloud_api_key_here"` passed silently | Added `_is_placeholder()` with 13 known placeholder substrings |
| 3 | `services/granite_service.py` | `_parse_evaluation` used `$` (end-of-line) in lookahead — `SAMPLE_ANSWER` as the last field was missed when response had no trailing newline | Changed `$` to `\Z` (absolute end-of-string) in all field regexes |
| 4 | `templates/dashboard.html` | `{{ s.student_name if s.student_name else '<span>—</span>' \| safe }}` — the `\| safe` applied to the whole ternary expression, enabling XSS | Used a proper `{%- if -%}` block with `{{ s.student_name \| e }}` |
| 5 | `templates/dashboard.html` | `by_role` data computed in `get_dashboard_stats()` but never rendered | Added "Performance by Role" table to the dashboard |
| 6 | `services/granite_service.py` | `_get_model()` called `_clear_model_cache()` inside its own `except WMLClientError` block — impossible since `lru_cache` never stores a failed call | Removed the unreachable `_clear_model_cache()` call; added explanatory comment |
