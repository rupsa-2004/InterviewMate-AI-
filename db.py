"""
database/db.py – SQLite connection helper, schema, and all data access helpers.

Tables
------
sessions  – one row per interview session (includes student_name)
questions – one row per question/answer pair within a session

Migration
---------
init_db() is safe to call on every app start.  It uses CREATE TABLE IF NOT EXISTS
for new installs, then runs ALTER TABLE statements (guarded by a column check) for
existing databases that predate a schema change.  This means the database file
survives Flask restarts and schema upgrades without data loss.
"""

import sqlite3
import os
from config import Config


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Return a new SQLite connection with Row factory and FK enforcement."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # safer for concurrent reads
    return conn


# ---------------------------------------------------------------------------
# Schema initialisation + migration
# ---------------------------------------------------------------------------

def init_db() -> None:
    """
    Create tables if they do not exist, then run any pending migrations.
    Safe to call on every application start.
    """
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    # ── Create tables (new install) ──────────────────────────────────────────
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name    TEXT    NOT NULL DEFAULT '',
            role            TEXT    NOT NULL,
            interview_type  TEXT    NOT NULL,
            difficulty      TEXT    NOT NULL,
            total_questions INTEGER NOT NULL DEFAULT 0,
            average_score   REAL    DEFAULT 0.0,
            completed       INTEGER DEFAULT 0,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS questions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            question_number INTEGER NOT NULL DEFAULT 1,
            question_text   TEXT    NOT NULL,
            answer_text     TEXT    DEFAULT '',
            score           REAL    DEFAULT 0.0,
            correctness     TEXT    DEFAULT '',
            clarity         TEXT    DEFAULT '',
            completeness    TEXT    DEFAULT '',
            strengths       TEXT    DEFAULT '',
            improvements    TEXT    DEFAULT '',
            sample_answer   TEXT    DEFAULT '',
            evaluated       INTEGER DEFAULT 0
        );
    """)

    # ── Migrations for existing databases ───────────────────────────────────
    _migrate(cursor)

    conn.commit()
    conn.close()


def _migrate(cursor: sqlite3.Cursor) -> None:
    """
    Apply any schema changes that were added after the initial release.
    Each ALTER TABLE is guarded: it only runs if the column does not yet exist.
    New migrations must be appended here.
    """
    existing_cols = {row[1] for row in cursor.execute("PRAGMA table_info(sessions)")}

    if "student_name" not in existing_cols:
        cursor.execute(
            "ALTER TABLE sessions ADD COLUMN student_name TEXT NOT NULL DEFAULT ''"
        )


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def create_session(
    role: str,
    interview_type: str,
    difficulty: str,
    total_questions: int,
    student_name: str = "",
) -> int:
    """
    Insert a new session row and return its id.

    Parameters
    ----------
    role, interview_type, difficulty, total_questions : interview configuration
    student_name : optional name entered on the setup form (defaults to '')
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO sessions
               (student_name, role, interview_type, difficulty, total_questions)
           VALUES (?, ?, ?, ?, ?)""",
        (student_name.strip(), role, interview_type, difficulty, total_questions),
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def complete_session(session_id: int) -> None:
    """Mark a session as completed and recompute its average score."""
    conn = get_db()
    conn.execute(
        """UPDATE sessions
           SET completed     = 1,
               average_score = (
                   SELECT ROUND(AVG(score), 1)
                   FROM questions
                   WHERE session_id = ? AND evaluated = 1
               )
           WHERE id = ?""",
        (session_id, session_id),
    )
    conn.commit()
    conn.close()


def get_session(session_id: int) -> dict | None:
    """Return a single session row as a dict, or None if not found."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Question helpers
# ---------------------------------------------------------------------------

def save_questions(session_id: int, questions: list[str]) -> None:
    """Insert a list of question strings for the given session."""
    conn = get_db()
    cursor = conn.cursor()
    for i, question_text in enumerate(questions, start=1):
        cursor.execute(
            """INSERT INTO questions (session_id, question_number, question_text)
               VALUES (?, ?, ?)""",
            (session_id, i, question_text),
        )
    conn.commit()
    conn.close()


def save_answer(question_id: int, answer_text: str, evaluation: dict) -> None:
    """
    Update a question row with the user's answer and AI evaluation result.

    evaluation keys: score, correctness, clarity, completeness,
                     strengths, improvements, sample_answer
    """
    conn = get_db()
    conn.execute(
        """UPDATE questions
           SET answer_text   = ?,
               score         = ?,
               correctness   = ?,
               clarity       = ?,
               completeness  = ?,
               strengths     = ?,
               improvements  = ?,
               sample_answer = ?,
               evaluated     = 1
           WHERE id = ?""",
        (
            answer_text,
            evaluation.get("score", 0.0),
            evaluation.get("correctness", ""),
            evaluation.get("clarity", ""),
            evaluation.get("completeness", ""),
            evaluation.get("strengths", ""),
            evaluation.get("improvements", ""),
            evaluation.get("sample_answer", ""),
            question_id,
        ),
    )
    conn.commit()
    conn.close()


def get_questions(session_id: int) -> list[dict]:
    """Return all question rows for a session, ordered by question_number."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM questions WHERE session_id = ? ORDER BY question_number",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Dashboard helpers
# ---------------------------------------------------------------------------

def get_dashboard_stats() -> dict:
    """
    Return aggregate statistics for the dashboard.

    Counts only completed sessions and only evaluated answers,
    so partially completed sessions do not pollute the stats.
    """
    conn = get_db()

    # Overall totals
    row = conn.execute(
        """SELECT
               COUNT(DISTINCT s.id)           AS total_sessions,
               COUNT(q.id)                    AS total_answers,
               ROUND(AVG(q.score), 1)         AS avg_score
           FROM sessions s
           INNER JOIN questions q
               ON q.session_id = s.id AND q.evaluated = 1
           WHERE s.completed = 1"""
    ).fetchone()

    stats = dict(row) if row else {}
    stats.setdefault("total_sessions", 0)
    stats.setdefault("total_answers", 0)
    stats.setdefault("avg_score", 0.0)

    # If no evaluated answers yet, total_sessions should still count correctly
    if stats["total_sessions"] == 0:
        count_row = conn.execute(
            "SELECT COUNT(*) AS n FROM sessions WHERE completed = 1"
        ).fetchone()
        stats["total_sessions"] = count_row["n"] if count_row else 0

    # Per-role breakdown (for dashboard chart / table)
    role_rows = conn.execute(
        """SELECT s.role,
                  COUNT(DISTINCT s.id)      AS sessions,
                  ROUND(AVG(q.score), 1)    AS avg_score
           FROM sessions s
           INNER JOIN questions q
               ON q.session_id = s.id AND q.evaluated = 1
           WHERE s.completed = 1
           GROUP BY s.role
           ORDER BY sessions DESC"""
    ).fetchall()
    stats["by_role"] = [dict(r) for r in role_rows]

    conn.close()
    return stats


def get_history() -> list[dict]:
    """
    Return all completed sessions newest-first, including student_name.
    Used by the dashboard history table.
    """
    conn = get_db()
    rows = conn.execute(
        """SELECT id, student_name, role, interview_type, difficulty,
                  total_questions, average_score, created_at
           FROM sessions
           WHERE completed = 1
           ORDER BY created_at DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_with_questions(session_id: int) -> dict | None:
    """
    Return a session dict that also contains a 'questions' key with all
    associated question/answer/feedback rows.  Useful for the results page.
    """
    session = get_session(session_id)
    if session is None:
        return None
    session["questions"] = get_questions(session_id)
    return session
