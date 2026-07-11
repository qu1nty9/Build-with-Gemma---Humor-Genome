from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.schemas import ComedyGene, MutationRequest, MutationResponse

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

    for variant in response.variants:
        candidate_normalized = normalized(variant.text)
        prefix = f"{variant.label}:"

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

