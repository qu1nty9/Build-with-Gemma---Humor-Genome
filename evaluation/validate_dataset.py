from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from app.schemas import ComedyGene, HumorMechanism
from app.validation import normalized

ALLOWED_LICENSES = {"CC0-1.0", "CC-BY-4.0", "public-domain"}
CALIBRATED_GENES = {ComedyGene.BREVITY}
REVALIDATION_GENES = {ComedyGene.MISDIRECTION}


class EvaluationExample(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9]+(?:_[a-z0-9]+)*_\d{3}$", max_length=80)
    text: str = Field(min_length=8, max_length=500)
    source: str = Field(min_length=3, max_length=120)
    license: str = Field(min_length=3, max_length=40)
    split: Literal["seed", "evaluation", "demo"]
    calibration_status: Literal["calibrated", "revalidation", "experimental"]
    target_gene: ComedyGene
    expected_mechanisms: list[HumorMechanism] = Field(min_length=1, max_length=4)


def validate_examples(path: Path, minimum_examples: int = 1) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    examples: list[EvaluationExample] = []

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            examples.append(EvaluationExample.model_validate_json(line))
        except ValidationError as exc:
            errors.append(f"line {line_number}: {exc}")

    ids = [example.id for example in examples]
    duplicate_ids = sorted(identifier for identifier, count in Counter(ids).items() if count > 1)
    if duplicate_ids:
        errors.append(f"duplicate ids: {duplicate_ids}")

    normalized_texts = [normalized(example.text) for example in examples]
    duplicate_texts = sorted(text for text, count in Counter(normalized_texts).items() if count > 1)
    if duplicate_texts:
        errors.append(f"duplicate normalized texts: {duplicate_texts}")

    for example in examples:
        if example.license not in ALLOWED_LICENSES:
            errors.append(f"{example.id}: unsupported license {example.license!r}")
        should_be_calibrated = example.target_gene in CALIBRATED_GENES
        if example.calibration_status == "calibrated" and not should_be_calibrated:
            errors.append(f"{example.id}: {example.target_gene.value} is not a calibrated gene")
        if example.calibration_status == "experimental" and should_be_calibrated:
            warnings.append(f"{example.id}: calibrated gene is marked experimental")
        if example.calibration_status == "revalidation" and example.target_gene not in REVALIDATION_GENES:
            errors.append(f"{example.id}: {example.target_gene.value} is not currently under revalidation")

    if len(examples) < minimum_examples:
        errors.append(f"dataset has {len(examples)} examples; minimum is {minimum_examples}")

    return {
        "status": "ok" if not errors else "error",
        "examples": len(examples),
        "errors": errors,
        "warnings": warnings,
        "licenses": dict(sorted(Counter(example.license for example in examples).items())),
        "splits": dict(sorted(Counter(example.split for example in examples).items())),
        "target_genes": dict(sorted(Counter(example.target_gene.value for example in examples).items())),
        "calibration_status": dict(
            sorted(Counter(example.calibration_status for example in examples).items())
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Humor Genome evaluation dataset metadata.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--min-examples", type=int, default=1)
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    report = validate_examples(args.input, args.min_examples)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
