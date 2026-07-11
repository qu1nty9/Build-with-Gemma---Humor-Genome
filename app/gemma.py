from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import Settings

SchemaT = TypeVar("SchemaT", bound=BaseModel)
PROMPT_DIR = Path(__file__).parent / "prompts"


class ModelGateway(Protocol):
    model_name: str

    async def generate(self, *, prompt_name: str, user_payload: dict, schema: type[SchemaT]) -> SchemaT:
        """Generate and validate one structured model response."""


class GemmaError(RuntimeError):
    """Raised when Gemma inference or validation fails."""


class GemmaQualityError(GemmaError):
    """Raised when Gemma cannot satisfy a semantic output invariant after repair."""


class OllamaGemmaGateway:
    def __init__(self, settings: Settings) -> None:
        self.model_name = settings.gemma_model
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.timeout = settings.timeout_seconds
        self.max_output_tokens = settings.max_output_tokens
        self.context_tokens = settings.context_tokens

    @staticmethod
    def _load_prompt(prompt_name: str) -> str:
        path = PROMPT_DIR / f"{prompt_name}.txt"
        if not path.is_file():
            raise GemmaError(f"Unknown prompt: {prompt_name}")
        return path.read_text(encoding="utf-8").strip()

    @staticmethod
    def _extract_json(content: str) -> str:
        """Remove common presentation wrappers without changing the JSON payload."""
        cleaned = content.strip()
        if cleaned.startswith("```"):
            first_newline = cleaned.find("\n")
            if first_newline != -1:
                cleaned = cleaned[first_newline + 1 :]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        object_start = cleaned.find("{")
        object_end = cleaned.rfind("}")
        if object_start > 0 and object_end > object_start:
            cleaned = cleaned[object_start : object_end + 1]
        return cleaned

    async def _chat(self, messages: list[dict[str, str]], schema: type[SchemaT]) -> str:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "think": False,
            "format": schema.model_json_schema(),
            "keep_alive": "15m",
            "options": {
                "temperature": 0.35,
                "top_p": 0.9,
                "seed": 42,
                "num_predict": self.max_output_tokens,
                "num_ctx": self.context_tokens,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GemmaError(f"Ollama request failed: {exc}") from exc

        try:
            return response.json()["message"]["content"]
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise GemmaError("Ollama returned an unexpected response shape") from exc

    async def generate(self, *, prompt_name: str, user_payload: dict, schema: type[SchemaT]) -> SchemaT:
        system_prompt = self._load_prompt(prompt_name)
        output_schema = schema.model_json_schema()
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task_input": user_payload,
                        "required_output_schema": output_schema,
                        "instruction": "Return every required field using exactly these field names and enum values.",
                    },
                    ensure_ascii=False,
                ),
            },
        ]
        content = await self._chat(messages, schema)
        try:
            return schema.model_validate_json(self._extract_json(content))
        except ValidationError as first_error:
            repair_messages = [
                *messages,
                {"role": "assistant", "content": content},
                {
                    "role": "user",
                    "content": (
                        "Repair the previous output so it matches the JSON schema exactly. "
                        "Return all required fields and only allowed enum values. "
                        f"JSON schema: {json.dumps(output_schema, ensure_ascii=False)}. "
                        f"Validation error: {first_error}"
                    ),
                },
            ]
            repaired = await self._chat(repair_messages, schema)
            try:
                return schema.model_validate_json(self._extract_json(repaired))
            except ValidationError as second_error:
                messages = " ".join(error["msg"] for error in second_error.errors())
                if "one-gene self-check" in messages or "requested target_gene" in messages:
                    raise GemmaQualityError(messages) from second_error
                raise GemmaError(f"Gemma returned invalid structured output after repair: {second_error}") from second_error
