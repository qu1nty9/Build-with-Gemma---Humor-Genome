from __future__ import annotations

import argparse
import asyncio
import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.config import settings
from app.gemma import GemmaError, OllamaGemmaGateway


GENE_CONTRACTS = {
    "brevity": "Only remove or compress wording; preserve premise, turn, punchline meaning, mechanism, and voice.",
    "specificity": "Replace a broad existing detail with a concrete observable detail without adding a new event, character, stake, mechanism, or joke.",
    "misdirection": "Change how the existing expectation points toward the existing reveal; preserve premise, payoff meaning, tone, and detail level.",
    "punchline": "Rewrite only the final payoff; preserve setup, premise, voice, and the existing mechanism.",
    "callback": "Add or strengthen only a reference to material already present.",
    "timing": "Change only pause, order, sentence boundary, or reveal placement.",
    "tone": "Change only stylistic attitude; preserve events, details, mechanism, and payoff meaning.",
    "cultural_accessibility": "Replace or explain only a culture-bound reference while preserving the joke mechanism.",
}


class VariantTeacherAudit(BaseModel):
    label: str = Field(min_length=1, max_length=20)
    target_gene_isolated: bool
    premise_preserved: bool
    non_target_mechanisms_preserved: bool
    meaningful_edit: bool
    failure_modes: list[str] = Field(default_factory=list, max_length=4)
    rationale: str = Field(min_length=1, max_length=800)
    confidence: float = Field(ge=0, le=1)


class TeacherAuditResponse(BaseModel):
    audits: list[VariantTeacherAudit] = Field(min_length=2, max_length=3)
    overall_assessment: str = Field(min_length=1, max_length=800)
    limitations: list[str] = Field(min_length=1, max_length=4)


def load_records(paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        records.extend(
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    return records


def audit_issues(variants: list[dict], response: TeacherAuditResponse) -> list[str]:
    expected = [variant["label"] for variant in variants]
    observed = [audit.label for audit in response.audits]
    issues: list[str] = []
    if len(observed) != len(expected):
        issues.append(f"Expected {len(expected)} audits, received {len(observed)}")
    if sorted(observed) != sorted(expected):
        issues.append(f"Audit labels must match variants exactly once: expected {expected}, received {observed}")
    return issues


async def audit_record(record: dict[str, Any], gateway: OllamaGemmaGateway) -> dict[str, Any]:
    started = time.perf_counter()
    output = {
        "id": record.get("id"),
        "candidate_model": record.get("model"),
        "candidate_method": record.get("method", "humor_genome_pipeline"),
        "teacher_model": gateway.model_name,
        "target_gene": record.get("target_gene"),
    }
    if record.get("status") != "ok" or "mutation" not in record.get("result", {}):
        output.update(status="skipped", error="Candidate record has no successful mutation")
        output["latency_seconds"] = 0.0
        return output

    mutation = record["result"]["mutation"]
    payload = {
        "source_text": mutation["source_text"],
        "target_gene": record["target_gene"],
        "gene_contract": GENE_CONTRACTS[record["target_gene"]],
        "variants": mutation["variants"],
    }
    try:
        response = await gateway.generate(
            prompt_name="teacher_audit_v1",
            user_payload=payload,
            schema=TeacherAuditResponse,
        )
        issues = audit_issues(mutation["variants"], response)
        if issues:
            payload["validator_feedback"] = issues
            response = await gateway.generate(
                prompt_name="teacher_audit_v1",
                user_payload=payload,
                schema=TeacherAuditResponse,
            )
            issues = audit_issues(mutation["variants"], response)
        if issues:
            output.update(status="error", error="; ".join(issues))
        else:
            output.update(status="ok", audit=response.model_dump(mode="json"))
    except GemmaError as exc:
        output.update(status="error", error=str(exc))
    output["latency_seconds"] = round(time.perf_counter() - started, 3)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit mutation outputs with a slower Gemma teacher.")
    parser.add_argument("--input", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--teacher-model", default="gemma4:12b")
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    records = load_records(args.input)
    if args.limit is not None:
        records = records[: args.limit]
    gateway = OllamaGemmaGateway(replace(settings, gemma_model=args.teacher_model))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as output_file:
        for record in records:
            result = await audit_record(record, gateway)
            output_file.write(json.dumps(result, ensure_ascii=False) + "\n")
            output_file.flush()
            print(f"{result['id']}: {result['status']} ({result['latency_seconds']}s)")


if __name__ == "__main__":
    asyncio.run(run())
