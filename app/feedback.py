from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.schemas import FeedbackReceipt, FeedbackRequest


class FeedbackStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                experiment_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                source_text TEXT NOT NULL,
                target_gene TEXT NOT NULL,
                variants_json TEXT NOT NULL,
                chosen_variant_label TEXT NOT NULL,
                blind_label TEXT NOT NULL,
                model TEXT NOT NULL
            )
            """
        )
        return connection

    def save(self, request: FeedbackRequest) -> FeedbackReceipt:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO feedback (
                    experiment_id, created_at, source_text, target_gene, variants_json,
                    chosen_variant_label, blind_label, model
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.experiment_id,
                    datetime.now(UTC).isoformat(),
                    request.source_text,
                    request.target_gene.value,
                    json.dumps([variant.model_dump(mode="json") for variant in request.variants], ensure_ascii=False),
                    request.chosen_variant_label,
                    request.blind_label,
                    request.model,
                ),
            )
        return FeedbackReceipt(experiment_id=request.experiment_id, saved=True)

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) FROM feedback").fetchone()
        return int(row[0]) if row else 0

