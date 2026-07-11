from app.schemas import ComedyGene, HumorGenome, MutationRequest, MutationResponse, MutationVariant
from app.validation import lexical_similarity, mutation_issues, word_count


def genome(source: str) -> HumorGenome:
    return HumorGenome(
        input_text=source,
        language="English",
        premise="A smart fridge monitors its owner.",
        setup="A smart fridge offers health advice.",
        assumptions=["The advice will be sophisticated."],
        turn="The advice is simply to avoid the fridge.",
        punchline="stop opening the fridge",
        mechanisms=[
            {
                "mechanism": "misdirection",
                "evidence": "The promised technology gives obvious advice.",
                "role": "Reverses the expectation.",
                "confidence": 0.9,
            }
        ],
        confidence=0.9,
    )


def variant(label: str, text: str) -> MutationVariant:
    return MutationVariant(
        label=label,
        text=text,
        changed_gene=ComedyGene.BREVITY,
        change_summary="Shortened the setup.",
        preserved_invariants=["preserve the premise"],
        changed_only_target_gene=True,
        confidence=0.8,
    )


def test_text_metrics() -> None:
    assert word_count("One, two-three") == 2
    assert lexical_similarity("same small joke", "same small joke") == 1


def test_brevity_variants_pass_when_shorter_and_distinct() -> None:
    source = "My smart fridge sends me health tips. Mostly it recommends I stop opening the fridge."
    request = MutationRequest(source_text=source, genome=genome(source), target_gene=ComedyGene.BREVITY)
    response = MutationResponse(
        source_text=source,
        target_gene=ComedyGene.BREVITY,
        variants=[
            variant("A", "My smart fridge's health tip: stop opening it."),
            variant("B", "My fridge tracks my health by asking me to leave it closed."),
        ],
    )
    assert mutation_issues(request, response) == []


def test_brevity_variant_fails_when_longer() -> None:
    source = "My smart fridge tells me to stop opening it."
    request = MutationRequest(source_text=source, genome=genome(source), target_gene=ComedyGene.BREVITY)
    response = MutationResponse(
        source_text=source,
        target_gene=ComedyGene.BREVITY,
        variants=[
            variant("A", "My smart fridge tells me every single morning that I should really stop opening it so often."),
            variant("B", "My fridge says: stop opening me."),
        ],
    )
    issues = mutation_issues(request, response)
    assert any("must be shorter" in issue for issue in issues)


def test_failed_model_self_check_is_a_quality_issue() -> None:
    source = "My smart fridge tells me to stop opening it."
    request = MutationRequest(source_text=source, genome=genome(source), target_gene=ComedyGene.BREVITY)
    failed = variant("A", "My fridge says: stop opening me.")
    failed.changed_only_target_gene = False
    response = MutationResponse(
        source_text=source,
        target_gene=ComedyGene.BREVITY,
        variants=[failed, variant("B", "My fridge says: keep it closed.")],
    )
    assert any("model self-check" in issue for issue in mutation_issues(request, response))
