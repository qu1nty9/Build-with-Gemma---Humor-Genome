import pytest
from pydantic import ValidationError

from app.schemas import ComedyGene, MutationResponse, MutationVariant


def make_variant(gene: ComedyGene, label: str) -> MutationVariant:
    return MutationVariant(
        label=label,
        text=f"Variant {label} text",
        changed_gene=gene,
        change_summary="Changed one target gene.",
        preserved_invariants=["preserve the premise"],
        changed_only_target_gene=True,
        confidence=0.8,
    )


def test_mutation_response_accepts_matching_genes() -> None:
    response = MutationResponse(
        source_text="A valid source joke.",
        target_gene=ComedyGene.BREVITY,
        variants=[
            make_variant(ComedyGene.BREVITY, "A"),
            make_variant(ComedyGene.BREVITY, "B"),
        ],
    )
    assert len(response.variants) == 2


def test_mutation_response_rejects_wrong_gene() -> None:
    with pytest.raises(ValidationError, match="requested target_gene"):
        MutationResponse(
            source_text="A valid source joke.",
            target_gene=ComedyGene.BREVITY,
            variants=[
                make_variant(ComedyGene.BREVITY, "A"),
                make_variant(ComedyGene.TONE, "B"),
            ],
        )


def test_mutation_response_rejects_failed_one_gene_check() -> None:
    failed = make_variant(ComedyGene.BREVITY, "B")
    failed.changed_only_target_gene = False
    with pytest.raises(ValidationError, match="one-gene self-check"):
        MutationResponse(
            source_text="A valid source joke.",
            target_gene=ComedyGene.BREVITY,
            variants=[make_variant(ComedyGene.BREVITY, "A"), failed],
        )
