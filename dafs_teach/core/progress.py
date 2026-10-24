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
                    solution_views INTEGER DEFAULT 0,
                    last_code     TEXT,
                    timestamp     TEXT,
                    PRIMARY KEY (student_name, lesson_id, exercise_id)
                )
            """)
            existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(progress)")}
            if "solution_views" not in existing_cols:
                conn.execute("ALTER TABLE progress ADD COLUMN solution_views INTEGER DEFAULT 0")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS sent_deadlines (
                    deadline_id TEXT PRIMARY KEY,
                    sent_at     TEXT
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

    def record_solution_view(self, student: str, lesson_id: str, exercise_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO progress (student_name, lesson_id, exercise_id, completed, attempts, solution_views, last_code, timestamp)
                VALUES (?, ?, ?, 0, 0, 1, '', ?)
                ON CONFLICT(student_name, lesson_id, exercise_id) DO UPDATE SET
                    solution_views = solution_views + 1,
                    timestamp      = excluded.timestamp
            """, (student, lesson_id, exercise_id, datetime.now().isoformat()))

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
        """Returns {lesson_id: {exercise_id: {completed, attempts, solution_views}}}"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT lesson_id, exercise_id, completed, attempts, solution_views
                FROM progress WHERE student_name = ?
            """, (student,)).fetchall()
        progress: dict = {}
        for lesson_id, ex_id, completed, attempts, solution_views in rows:
            progress.setdefault(lesson_id, {})[ex_id] = {
                "completed": bool(completed),
                "attempts": attempts,
                "solution_views": solution_views,
            }
        return progress

    def get_all_rows(self, student: str) -> list[dict]:
        """Returns one dict per (lesson, exercise) row — used for syncing to the instructor."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT lesson_id, exercise_id, completed, attempts, solution_views, timestamp
                FROM progress WHERE student_name = ?
            """, (student,)).fetchall()
        return [
            {
                "lesson_id": lesson_id,
                "exercise_id": exercise_id,
                "completed": bool(completed),
                "attempts": attempts,
                "solution_views": solution_views,
                "last_activity": timestamp,
            }
            for lesson_id, exercise_id, completed, attempts, solution_views, timestamp in rows
        ]

    def get_all_rows_any_student(self) -> list[dict]:
        """All progress rows regardless of student name — no name included.

        Used for anonymous, aggregate-only deadline reporting: this machine
        may only ever have one student's data on it, but the point is that
        the report itself carries no identity, by construction.
        """
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT lesson_id, exercise_id, completed, attempts, solution_views
                FROM progress
            """).fetchall()
        return [
            {
                "lesson_id": lesson_id,
                "exercise_id": exercise_id,
                "completed": bool(completed),
                "attempts": attempts,
                "solution_views": solution_views,
            }
            for lesson_id, exercise_id, completed, attempts, solution_views in rows
        ]

    def has_sent_deadline(self, deadline_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM sent_deadlines WHERE deadline_id = ?", (deadline_id,)
            ).fetchone()
        return row is not None

    def mark_deadline_sent(self, deadline_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sent_deadlines (deadline_id, sent_at) VALUES (?, ?)",
                (deadline_id, datetime.now().isoformat()),
            )
