from __future__ import annotations

import argparse
import asyncio
import json
import time
from dataclasses import replace
from pathlib import Path

from app.config import settings
from app.gemma import GemmaError, OllamaGemmaGateway
from app.pipeline import HumorGenomePipeline
from app.schemas import AnalyzeRequest
from evaluation.run_smoke import load_examples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare HumorGenome analysis across Gemma model variants.")
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def mechanism_names(record: dict) -> set[str]:
    if record.get("status") != "ok":
        return set()
    return {item["mechanism"] for item in record["result"]["mechanisms"]}


def mechanism_jaccard(left: dict, right: dict) -> float | None:
    left_names = mechanism_names(left)
    right_names = mechanism_names(right)
    if not left_names and not right_names:
        return None
    return len(left_names & right_names) / len(left_names | right_names)


async def evaluate_model(model: str, examples: list[dict]) -> list[dict]:
    model_settings = replace(settings, gemma_model=model)
    pipeline = HumorGenomePipeline(OllamaGemmaGateway(model_settings))
    records: list[dict] = []
    for example in examples:
        started = time.perf_counter()
        record = {"id": example["id"], "model": model, "stage": "analyze"}
        try:
            result = await pipeline.analyze(AnalyzeRequest(text=example["text"]))
            record.update(status="ok", result=result.model_dump(mode="json"))
        except GemmaError as exc:
            record.update(status="error", error=str(exc))
        record["latency_seconds"] = round(time.perf_counter() - started, 3)
        records.append(record)
        print(f"{model} / {example['id']}: {record['status']} ({record['latency_seconds']}s)")
    return records


def print_pair_summary(records: list[dict], models: list[str]) -> None:
    if len(models) != 2:
        return
    by_key = {(record["model"], record["id"]): record for record in records}
    ids = sorted({record["id"] for record in records})
    for example_id in ids:
        left = by_key.get((models[0], example_id))
        right = by_key.get((models[1], example_id))
        if left is None or right is None:
            continue
        agreement = mechanism_jaccard(left, right)
        rendered = "n/a" if agreement is None else f"{agreement:.2f}"
        print(f"agreement / {example_id}: {rendered}")


async def run() -> None:
    args = parse_args()
    examples = load_examples(args.input, args.limit)
    records: list[dict] = []
    for model in args.models:
        records.extend(await evaluate_model(model, examples))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as output:
        for record in records:
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
    print_pair_summary(records, args.models)


if __name__ == "__main__":
    asyncio.run(run())

