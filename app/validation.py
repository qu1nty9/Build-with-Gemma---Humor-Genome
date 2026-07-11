from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.schemas import ComedyGene, CompareRequest, ComparisonResponse, MutationRequest, MutationResponse

WORD_PATTERN = re.compile(r"\b[\w'-]+\b", flags=re.UNICODE)


def word_count(text: str) -> int:
    return len(WORD_PATTERN.findall(text))


def normalized(text: str) -> str:
    return " ".join(WORD_PATTERN.findall(text.lower()))


def lexical_similarity(source: str, candidate: str) -> float:
    return SequenceMatcher(None, normalized(source), normalized(candidate)).ratio()


def mutation_issues(request: MutationRequest, response: MutationResponse) -> list[str]:
    """Return deterministic failures that should trigger one regeneration attempt."""
    issues: list[str] = []
    source_normalized = normalized(request.source_text)
    source_words = word_count(request.source_text)
    seen_variants: set[str] = set()
    seen_labels: set[str] = set()

    for variant in response.variants:
        candidate_normalized = normalized(variant.text)
        prefix = f"{variant.label}:"
        label_key = variant.label.strip().casefold()

        if label_key in seen_labels:
            issues.append(f"{prefix} label duplicates another variant; every label must be unique")
        seen_labels.add(label_key)
        if variant.changed_gene != request.target_gene:
            issues.append(
                f"{prefix} changed_gene is {variant.changed_gene.value}; it must match requested {request.target_gene.value}"
            )
        if not variant.changed_only_target_gene:
            issues.append(f"{prefix} model self-check reports that more than the target gene changed")
        if candidate_normalized == source_normalized:
            issues.append(f"{prefix} identical to the source")
        if candidate_normalized in seen_variants:
            issues.append(f"{prefix} duplicates another variant")
        seen_variants.add(candidate_normalized)

        similarity = lexical_similarity(request.source_text, variant.text)
        if similarity < 0.25:
            issues.append(f"{prefix} lexical similarity {similarity:.2f} is too low to preserve the source")

        if request.target_gene == ComedyGene.BREVITY:
            candidate_words = word_count(variant.text)
            if candidate_words >= source_words:
                issues.append(
                    f"{prefix} brevity edit has {candidate_words} words; it must be shorter than the {source_words}-word source"
                )

    if len(seen_variants) != request.number_of_variants:
        issues.append("The response does not contain the requested number of distinct variants")
    return issues


def comparison_issues(request: CompareRequest, response: ComparisonResponse) -> list[str]:
    """Ensure every submitted variant has exactly one matching observation."""
    expected = [variant.label for variant in request.variants]
    observed = [observation.label for observation in response.observations]
    issues: list[str] = []
    if len(observed) != len(expected):
        issues.append(f"Expected {len(expected)} observations, received {len(observed)}")
    if sorted(observed) != sorted(expected):
        issues.append(
            "Observation labels must match variant labels exactly once; "
            f"expected {expected}, received {observed}"
        )
    return issues
