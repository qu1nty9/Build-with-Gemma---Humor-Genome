from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from evaluation.run_teacher_audit import load_records
from evaluation.summarize_results import percentile, rounded


def audit_passes(audit: dict[str, Any]) -> bool:
    return all(
        audit.get(field) is True
        for field in (
            "target_gene_isolated",
            "premise_preserved",
            "non_target_mechanisms_preserved",
            "meaningful_edit",
        )
    )


def summarize_audits(records: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [record for record in records if record.get("status") == "ok"]
    audits = [audit for record in successful for audit in record["audit"]["audits"]]
    latencies = [float(record["latency_seconds"]) for record in successful]
    by_gene: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_method: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in successful:
        record_audits = record["audit"]["audits"]
        by_gene[str(record.get("target_gene", "unknown"))].extend(record_audits)
        by_method[str(record.get("candidate_method", "unknown"))].extend(record_audits)

    def rate(field: str, rows: list[dict[str, Any]]) -> float | None:
        return rounded(sum(row.get(field) is True for row in rows) / len(rows) if rows else None)

    return {
        "records_attempted": len(records),
        "records_audited": len(successful),
        "variants_audited": len(audits),
        "variant_pass_rate": rounded(sum(audit_passes(audit) for audit in audits) / len(audits) if audits else None),
        "target_gene_isolation_rate": rate("target_gene_isolated", audits),
        "premise_preservation_rate": rate("premise_preserved", audits),
        "mechanism_preservation_rate": rate("non_target_mechanisms_preserved", audits),
        "meaningful_edit_rate": rate("meaningful_edit", audits),
        "mean_teacher_confidence": rounded(
            statistics.fmean(float(audit["confidence"]) for audit in audits) if audits else None
        ),
        "teacher_latency_seconds": {
            "p50": rounded(statistics.median(latencies) if latencies else None),
            "p95": rounded(percentile(latencies, 0.95)),
        },
        "by_target_gene": {
            gene: {
                "variants": len(rows),
                "pass_rate": rounded(sum(audit_passes(row) for row in rows) / len(rows)),
                "target_gene_isolation_rate": rate("target_gene_isolated", rows),
            }
            for gene, rows in sorted(by_gene.items())
        },
        "by_candidate_method": {
            method: {
                "variants": len(rows),
                "pass_rate": rounded(sum(audit_passes(row) for row in rows) / len(rows)),
                "target_gene_isolation_rate": rate("target_gene_isolated", rows),
                "premise_preservation_rate": rate("premise_preserved", rows),
                "mechanism_preservation_rate": rate("non_target_mechanisms_preserved", rows),
            }
            for method, rows in sorted(by_method.items())
        },
    }


def percent(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Gemma teacher audit summary",
        "",
        "| Candidate method | Variants | Full rubric pass | Gene isolated |",
        "|---|---:|---:|---:|",
    ]
    for method, metrics in summary["by_candidate_method"].items():
        lines.append(
            f"| `{method}` | {metrics['variants']} | {percent(metrics['pass_rate'])} | "
            f"{percent(metrics['target_gene_isolation_rate'])} |"
        )
    lines.extend(
        [
            "",
            "## By target gene",
            "",
        "| Target gene | Variants | Full rubric pass | Gene isolated |",
        "|---|---:|---:|---:|",
        ]
    )
    for gene, metrics in summary["by_target_gene"].items():
        lines.append(
            f"| `{gene}` | {metrics['variants']} | {percent(metrics['pass_rate'])} | "
            f"{percent(metrics['target_gene_isolation_rate'])} |"
        )
    lines.extend(
        [
            "",
            f"Overall variant pass rate: **{percent(summary['variant_pass_rate'])}** "
            f"across {summary['variants_audited']} audited variants.",
            "",
            "> The 12B teacher is a model-based diagnostic, not ground truth and not a substitute for blind human preference.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize Gemma teacher-audit JSONL.")
    parser.add_argument("--input", type=Path, nargs="+", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    summary = summarize_audits(load_records(args.input))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(summary), encoding="utf-8")


if __name__ == "__main__":
    run()
