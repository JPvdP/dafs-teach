import sqlite3
from datetime import datetime
from pathlib import Path


class ProgressTracker:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS progress (
                    student_name  TEXT,
                    lesson_id     TEXT,
                    exercise_id   TEXT,
                    completed     INTEGER DEFAULT 0,
                    attempts      INTEGER DEFAULT 0,
                    last_code     TEXT,
                    timestamp     TEXT,
                    PRIMARY KEY (student_name, lesson_id, exercise_id)
                )
            """)

    def record_attempt(self, student: str, lesson_id: str, exercise_id: str, code: str, passed: bool):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO progress (student_name, lesson_id, exercise_id, completed, attempts, last_code, timestamp)
                VALUES (?, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(student_name, lesson_id, exercise_id) DO UPDATE SET
                    completed  = MAX(completed, excluded.completed),
                    attempts   = attempts + 1,
                    last_code  = excluded.last_code,
                    timestamp  = excluded.timestamp
            """, (student, lesson_id, exercise_id, int(passed), code, datetime.now().isoformat()))

    def get_completed(self, student: str, lesson_id: str) -> set:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT exercise_id FROM progress
                WHERE student_name = ? AND lesson_id = ? AND completed = 1
            """, (student, lesson_id)).fetchall()
        return {r[0] for r in rows}

    def get_last_code(self, student: str, lesson_id: str, exercise_id: str) -> str | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT last_code FROM progress
                WHERE student_name = ? AND lesson_id = ? AND exercise_id = ?
            """, (student, lesson_id, exercise_id)).fetchone()
        return row[0] if row else None

    def get_all_progress(self, student: str) -> dict:
        """Returns {lesson_id: {exercise_id: {completed, attempts}}}"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT lesson_id, exercise_id, completed, attempts
                FROM progress WHERE student_name = ?
            """, (student,)).fetchall()
        progress: dict = {}
        for lesson_id, ex_id, completed, attempts in rows:
            progress.setdefault(lesson_id, {})[ex_id] = {
                "completed": bool(completed),
                "attempts": attempts,
            }
        return progress
