import pytest
from pydantic import ValidationError

from app.feedback import FeedbackStore
from app.schemas import ComedyGene, FeedbackRequest, MutationVariant


def variant(label: str) -> MutationVariant:
    return MutationVariant(
        label=label,
        text=f"Short variant {label}.",
        changed_gene=ComedyGene.BREVITY,
        change_summary="Shortened wording.",
        preserved_invariants=["preserve the premise"],
        changed_only_target_gene=True,
        confidence=0.8,
    )


def request() -> FeedbackRequest:
    return FeedbackRequest(
        experiment_id="12345678-abcd",
        source_text="A source joke with enough text.",
        target_gene=ComedyGene.BREVITY,
        variants=[variant("A"), variant("B")],
        chosen_variant_label="A",
        blind_label="B",
        model="gemma4:e2b",
        consent=True,
    )


def test_feedback_store_saves_opted_in_choice(tmp_path) -> None:
    store = FeedbackStore(tmp_path / "feedback.sqlite3")
    receipt = store.save(request())
    assert receipt.saved is True
    assert store.count() == 1


def test_feedback_store_replaces_duplicate_experiment(tmp_path) -> None:
    store = FeedbackStore(tmp_path / "feedback.sqlite3")
    store.save(request())
    store.save(request())
    assert store.count() == 1


def test_feedback_requires_explicit_consent() -> None:
    payload = request().model_dump(mode="json")
    payload["consent"] = False
    with pytest.raises(ValidationError):
        FeedbackRequest.model_validate(payload)


def test_feedback_choice_must_match_a_variant() -> None:
    payload = request().model_dump(mode="json")
    payload["chosen_variant_label"] = "missing"
    with pytest.raises(ValidationError, match="must match"):
        FeedbackRequest.model_validate(payload)
