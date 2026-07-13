from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

from app.config import settings
from app.gemma import GemmaError, OllamaGemmaGateway
from app.schemas import ComedyGene, MutationResponse
from evaluation.run_smoke import load_examples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the one-shot no-genome mutation baseline.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--ids", nargs="+")
    return parser.parse_args()


def normalize_baseline_mutation(
    source_text: str,
    target_gene: str,
    mutation: MutationResponse,
) -> MutationResponse:
    variants = [
        variant.model_copy(update={"label": f"Variant {chr(65 + index)}"})
        for index, variant in enumerate(mutation.variants[:2])
    ]
    return mutation.model_copy(
        update={
            "source_text": source_text,
            "target_gene": ComedyGene(target_gene),
            "variants": variants,
        }
    )


async def run() -> None:
    args = parse_args()
    examples = load_examples(args.input, args.limit, args.ids)
    gateway = OllamaGemmaGateway(settings)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as output:
        for example in examples:
            started = time.perf_counter()
            record = {
                "id": example["id"],
                "model": settings.gemma_model,
                "method": "one_shot_no_genome",
                "target_gene": example["target_gene"],
                "source": example.get("source"),
                "license": example.get("license"),
            }
            try:
                mutation = await gateway.generate(
                    prompt_name="baseline_v1",
                    user_payload={
                        "source_text": example["text"],
                        "target_gene": example["target_gene"],
                        "number_of_variants": 2,
                    },
                    schema=MutationResponse,
                )
                mutation = normalize_baseline_mutation(example["text"], example["target_gene"], mutation)
                record.update(status="ok", result={"mutation": mutation.model_dump(mode="json")})
            except GemmaError as exc:
                record.update(status="error", error=str(exc))
            record["latency_seconds"] = round(time.perf_counter() - started, 3)
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
            output.flush()
            print(f"{record['id']}: {record['status']} ({record['latency_seconds']}s)")


if __name__ == "__main__":
    asyncio.run(run())
