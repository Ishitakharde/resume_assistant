"""
database.py
------------
Small SQLite layer for the Resume Assistant.

Two tables:
  - sessions: one row per uploaded resume (raw text + optional job description)
  - messages: chat history tied to a session, so a conversation has memory
              across turns (used to build the prompt context sent to Gemini)
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = "resume_assistant.db"


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_text TEXT NOT NULL,
                job_description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,          -- 'user' or 'assistant'
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
            """
        )
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_session(resume_text: str, job_description: str = "") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO sessions (resume_text, job_description) VALUES (?, ?)",
            (resume_text, job_description),
        )
        conn.commit()
        return cur.lastrowid


def update_job_description(session_id: int, job_description: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET job_description = ? WHERE id = ?",
            (job_description, session_id),
        )
        conn.commit()


def get_session(session_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return dict(row) if row else None


def add_message(session_id: int, role: str, content: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        conn.commit()


def get_history(session_id: int, limit: int = 20):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT role, content, created_at FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
