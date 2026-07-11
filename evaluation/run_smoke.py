from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

from app.config import settings
from app.gemma import GemmaError, OllamaGemmaGateway
from app.pipeline import HumorGenomePipeline, PipelineQualityError
from app.schemas import ComedyGene, FlowRequest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the structured Humor Genome flow over JSONL examples.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--ids", nargs="+", help="Run only the selected example IDs.")
    return parser.parse_args()


def load_examples(path: Path, limit: int | None, ids: list[str] | None = None) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if ids is not None:
        selected = set(ids)
        rows = [row for row in rows if row["id"] in selected]
    return rows[:limit] if limit is not None else rows


async def run() -> None:
    args = parse_args()
    examples = load_examples(args.input, args.limit, args.ids)
    pipeline = HumorGenomePipeline(OllamaGemmaGateway(settings))
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as output:
        for example in examples:
            started = time.perf_counter()
            record = {
                "id": example["id"],
                "model": settings.gemma_model,
                "target_gene": example["target_gene"],
                "source": example.get("source"),
                "license": example.get("license"),
            }
            try:
                result = await pipeline.flow(
                    FlowRequest(
                        text=example["text"],
                        target_gene=ComedyGene(example["target_gene"]),
                    )
                )
                record.update(status="ok", result=result.model_dump(mode="json"))
            except (GemmaError, PipelineQualityError) as exc:
                record.update(status="error", error=str(exc))
            record["latency_seconds"] = round(time.perf_counter() - started, 3)
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
            output.flush()
            print(f"{record['id']}: {record['status']} ({record['latency_seconds']}s)")


if __name__ == "__main__":
    asyncio.run(run())
