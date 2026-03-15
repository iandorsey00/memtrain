import os
import sqlite3
from datetime import datetime, timedelta, timezone

from memtrain.memtrain_common.models import ProgressRecord


class ProgressStore:
    """Persist per-item learner progress for adaptive sessions."""

    def __init__(self, csvfile):
        self.db_path = self.get_db_path(csvfile)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def get_db_path(self, csvfile):
        override = os.environ.get("MEMTRAIN_PROGRESS_DB")
        if override:
            return override

        csv_dir = os.path.dirname(os.path.abspath(csvfile)) or "."
        return os.path.join(csv_dir, ".memtrain-progress.sqlite3")

    def create_tables(self):
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS item_progress (
                          study_set_id TEXT,
                          item_id TEXT,
                          current_stage INTEGER NOT NULL DEFAULT 0,
                          mastery_score REAL NOT NULL DEFAULT 0.0,
                          success_streak INTEGER NOT NULL DEFAULT 0,
                          failure_count INTEGER NOT NULL DEFAULT 0,
                          lapse_count INTEGER NOT NULL DEFAULT 0,
                          average_response_time REAL NOT NULL DEFAULT 0.0,
                          reviews INTEGER NOT NULL DEFAULT 0,
                          last_seen_at TEXT,
                          next_due_at TEXT,
                          PRIMARY KEY (study_set_id, item_id))"""
        )
        self.conn.commit()

    def get_progress_map(self, study_set_id, item_ids):
        if not item_ids:
            return {}

        placeholders = ",".join("?" for _ in item_ids)
        params = [study_set_id] + list(item_ids)
        query = """SELECT * FROM item_progress
                   WHERE study_set_id = ?
                   AND item_id IN ({})""".format(
            placeholders
        )

        rows = self.conn.execute(query, params).fetchall()
        out = {}

        for row in rows:
            out[row["item_id"]] = ProgressRecord.from_mapping(dict(row))

        return out

    def update_progress(self, study_set_id, item_id, progress):
        progress_values = progress.to_mapping()
        self.conn.execute(
            """INSERT INTO item_progress(
                   study_set_id, item_id, current_stage, mastery_score,
                   success_streak, failure_count, lapse_count,
                   average_response_time, reviews, last_seen_at, next_due_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(study_set_id, item_id) DO UPDATE SET
                   current_stage = excluded.current_stage,
                   mastery_score = excluded.mastery_score,
                   success_streak = excluded.success_streak,
                   failure_count = excluded.failure_count,
                   lapse_count = excluded.lapse_count,
                   average_response_time = excluded.average_response_time,
                   reviews = excluded.reviews,
                   last_seen_at = excluded.last_seen_at,
                   next_due_at = excluded.next_due_at""",
            (
                study_set_id,
                item_id,
                progress_values["current_stage"],
                progress_values["mastery_score"],
                progress_values["success_streak"],
                progress_values["failure_count"],
                progress_values["lapse_count"],
                progress_values["average_response_time"],
                progress_values["reviews"],
                progress_values["last_seen_at"],
                progress_values["next_due_at"],
            ),
        )
        self.conn.commit()

    def now(self):
        return datetime.now(timezone.utc)

    def parse_datetime(self, value):
        if not value:
            return None
        return datetime.fromisoformat(value)

    def to_iso(self, value):
        if value is None:
            return None
        return value.isoformat()

    def next_due(self, stage, is_correct):
        now = self.now()

        if not is_correct:
            return self.to_iso(now + timedelta(minutes=10))

        intervals = {
            0: timedelta(hours=4),
            1: timedelta(hours=12),
            2: timedelta(days=1),
            3: timedelta(days=3),
            4: timedelta(days=7),
        }
        return self.to_iso(now + intervals.get(stage, timedelta(days=1)))
