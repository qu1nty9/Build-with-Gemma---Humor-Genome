from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from app.validation import normalized, word_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize Humor Genome JSONL evaluation runs.")
    parser.add_argument("--input", type=Path, nargs="+", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def load_records(paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        records.extend(
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    return records


def percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[rank]


def controlled_mutation_passes(record: dict[str, Any]) -> bool | None:
    if record.get("status") != "ok":
        return None
    result = record.get("result", {})
    mutation = result.get("mutation")
    if mutation is None:
        return None

    variants = mutation.get("variants", [])
    source = mutation.get("source_text", "")
    target_gene = mutation.get("target_gene") or record.get("target_gene")
    if len(variants) < 2:
        return False

    rendered = [normalized(variant.get("text", "")) for variant in variants]
    labels = [str(variant.get("label", "")).strip().casefold() for variant in variants]
    if not source or any(not text for text in rendered):
        return False
    if len(set(rendered)) != len(rendered):
        return False
    if any(not label for label in labels) or len(set(labels)) != len(labels):
        return False
    if any(text == normalized(source) for text in rendered):
        return False
    if any(variant.get("changed_gene") != target_gene for variant in variants):
        return False
    if any(variant.get("changed_only_target_gene") is not True for variant in variants):
        return False
    if target_gene == "brevity" and any(word_count(variant.get("text", "")) >= word_count(source) for variant in variants):
        return False
    return True


def rounded(value: float | None) -> float | None:
    return None if value is None else round(value, 3)


def summarize_group(records: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [record for record in records if record.get("status") == "ok"]
    latencies = [float(record["latency_seconds"]) for record in records if record.get("latency_seconds") is not None]
    controlled = [value for record in records if (value := controlled_mutation_passes(record)) is not None]
    full_flows = [record for record in successful if "mutation" in record.get("result", {})]
    variants = [
        variant
        for record in full_flows
        for variant in record["result"]["mutation"].get("variants", [])
    ]

    stage_latencies: dict[str, list[float]] = {}
    for record in full_flows:
        for stage, value in record["result"].get("stage_latency_seconds", {}).items():
            stage_latencies.setdefault(stage, []).append(float(value))

    licenses = [record.get("license") for record in records]
    return {
        "attempted": len(records),
        "succeeded": len(successful),
        "success_rate": rounded(len(successful) / len(records) if records else None),
        "full_flows": len(full_flows),
        "controlled_mutations_passed": sum(controlled),
        "controlled_mutation_pass_rate": rounded(sum(controlled) / len(controlled) if controlled else None),
        "variant_self_check_rate": rounded(
            sum(variant.get("changed_only_target_gene") is True for variant in variants) / len(variants)
            if variants
            else None
        ),
        "latency_seconds": {
            "mean": rounded(statistics.fmean(latencies) if latencies else None),
            "p50": rounded(statistics.median(latencies) if latencies else None),
            "p95": rounded(percentile(latencies, 0.95)),
            "max": rounded(max(latencies) if latencies else None),
        },
        "mean_stage_latency_seconds": {
            stage: rounded(statistics.fmean(values)) for stage, values in sorted(stage_latencies.items())
        },
        "licensed_record_rate": rounded(
            sum(isinstance(value, str) and bool(value.strip()) for value in licenses) / len(licenses)
            if licenses
            else None
        ),
        "target_gene_counts": dict(sorted(Counter(record.get("target_gene", "unknown") for record in records).items())),
        "errors": dict(sorted(Counter(record.get("error", "unknown") for record in records if record.get("status") != "ok").items())),
    }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    models = sorted({str(record.get("model", "unknown")) for record in records})
    return {
        "overall": summarize_group(records),
        "by_model": {
            model: summarize_group([record for record in records if str(record.get("model", "unknown")) == model])
            for model in models
        },
    }


def percent(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def seconds(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Humor Genome evaluation summary",
        "",
        "| Model | Runs | Success | Controlled mutation | p50, s | p95, s | Licensed records |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model, metrics in summary["by_model"].items():
        lines.append(
            f"| `{model}` | {metrics['attempted']} | {percent(metrics['success_rate'])} | "
            f"{percent(metrics['controlled_mutation_pass_rate'])} | "
            f"{seconds(metrics['latency_seconds']['p50'])} | {seconds(metrics['latency_seconds']['p95'])} | "
            f"{percent(metrics['licensed_record_rate'])} |"
        )

    overall = summary["overall"]
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Successful runs: {overall['succeeded']}/{overall['attempted']} ({percent(overall['success_rate'])}).",
            f"- Controlled mutations passed: {overall['controlled_mutations_passed']}/{overall['full_flows']} "
            f"({percent(overall['controlled_mutation_pass_rate'])}).",
            f"- Variant self-check rate: {percent(overall['variant_self_check_rate'])}.",
            "",
            "> These are engineering metrics, not objective measures of funniness. Human blind A/B preference must be reported separately.",
            "",
        ]
    )
    return "\n".join(lines)


def run() -> None:
    args = parse_args()
    result = summarize(load_records(args.input))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(result), encoding="utf-8")


if __name__ == "__main__":
    run()
