from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    gemma_model: str = os.getenv("GEMMA_MODEL", "gemma4:e2b")
    timeout_seconds: float = float(os.getenv("GEMMA_TIMEOUT_SECONDS", "180"))
    max_output_tokens: int = int(os.getenv("GEMMA_MAX_OUTPUT_TOKENS", "1200"))
    context_tokens: int = int(os.getenv("GEMMA_CONTEXT_TOKENS", "8192"))
    feedback_db_path: str = os.getenv("FEEDBACK_DB_PATH", "data/feedback.sqlite3")


settings = Settings()
