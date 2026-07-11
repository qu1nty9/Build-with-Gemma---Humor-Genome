from typing import TypeVar

from pydantic import BaseModel

from app.pipeline import HumorGenomePipeline
from app.schemas import (
    ComedyGene,
    ComparisonResponse,
    FlowRequest,
    HumorGenome,
    MutationResponse,
)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class FakeGateway:
    model_name = "fake-gemma"

    async def generate(self, *, prompt_name: str, user_payload: dict, schema: type[SchemaT]) -> SchemaT:
        if schema is HumorGenome:
            data = {
                "input_text": user_payload["text"],
                "language": "English",
                "premise": "Therapy costs money.",
                "setup": "The speaker worries about money.",
                "assumptions": ["Therapy should help with the stated problem."],
                "turn": "The proposed help creates another fee.",
                "punchline": "for the usual fee",
                "mechanisms": [
                    {
                        "mechanism": "incongruity",
                        "evidence": "The treatment repeats the financial problem.",
                        "role": "Creates the contradiction.",
                        "confidence": 0.9,
                    }
                ],
                "timing_notes": ["Pause before the final clause."],
                "cultural_dependencies": [],
                "risks": [],
                "confidence": 0.88,
                "alternative_readings": [],
            }
        elif schema is MutationResponse:
            gene = user_payload["target_gene"]
            data = {
                "source_text": user_payload["source_text"],
                "target_gene": gene,
                "variants": [
                    {
                        "label": label,
                        "text": text,
                        "changed_gene": gene,
                        "change_summary": "Only the requested gene changed.",
                        "preserved_invariants": user_payload["invariants"],
                        "changed_only_target_gene": True,
                        "confidence": 0.8,
                    }
                    for label, text in [
                        ("A", "I worry about money. My therapist charged me to continue."),
                        ("B", "I told my therapist money worries me. Continuing cost extra."),
                    ]
                ],
                "caveats": [],
            }
        elif schema is ComparisonResponse:
            data = {
                "observations": [
                    {
                        "label": variant["label"],
                        "mechanism_effect": "The selected gene is easier to isolate.",
                        "likely_strengths": ["Controlled change"],
                        "likely_weaknesses": ["Requires human testing"],
                        "uncertainty": "Taste varies by audience.",
                    }
                    for variant in user_payload["variants"]
                ],
                "key_tradeoff": "Clarity versus surprise.",
                "suggested_human_test": "Use a blind pairwise comparison.",
                "limitations": ["This does not predict objective funniness."],
            }
        else:
            raise AssertionError(f"Unexpected schema: {schema}")
        return schema.model_validate(data)


class ExtraVariantGateway(FakeGateway):
    async def generate(self, *, prompt_name: str, user_payload: dict, schema: type[SchemaT]) -> SchemaT:
        result = await super().generate(prompt_name=prompt_name, user_payload=user_payload, schema=schema)
        if schema is MutationResponse:
            extra = result.variants[1].model_copy(update={"label": "C", "text": "My therapist charged extra to discuss money."})
            return result.model_copy(update={"variants": [*result.variants, extra]})
        return result


class RepairingComparisonGateway(FakeGateway):
    comparison_calls = 0

    async def generate(self, *, prompt_name: str, user_payload: dict, schema: type[SchemaT]) -> SchemaT:
        result = await super().generate(prompt_name=prompt_name, user_payload=user_payload, schema=schema)
        if schema is ComparisonResponse:
            self.comparison_calls += 1
            if "validator_feedback" not in user_payload:
                duplicate = result.observations[0].model_copy()
                return result.model_copy(update={"observations": [duplicate, duplicate]})
        return result


class RepairingMutationGateway(FakeGateway):
    mutation_calls = 0

    async def generate(self, *, prompt_name: str, user_payload: dict, schema: type[SchemaT]) -> SchemaT:
        result = await super().generate(prompt_name=prompt_name, user_payload=user_payload, schema=schema)
        if schema is MutationResponse:
            self.mutation_calls += 1
            if "validator_feedback" not in user_payload:
                wrong = result.variants[0].model_copy(update={"changed_gene": ComedyGene.TONE})
                return result.model_copy(update={"variants": [wrong, result.variants[1]]})
        return result


async def test_complete_flow() -> None:
    pipeline = HumorGenomePipeline(FakeGateway())
    result = await pipeline.flow(
        FlowRequest(
            text="I told my therapist I worry about money. She charged me to continue.",
            target_gene=ComedyGene.BREVITY,
        )
    )
    assert result.model == "fake-gemma"
    assert result.mutation.target_gene == ComedyGene.BREVITY
    assert len(result.comparison.observations) == 2


async def test_mutation_trims_extra_model_variants() -> None:
    pipeline = HumorGenomePipeline(ExtraVariantGateway())
    result = await pipeline.flow(
        FlowRequest(
            text="I told my therapist I worry about money. She charged me to continue.",
            target_gene=ComedyGene.BREVITY,
            number_of_variants=2,
        )
    )
    assert [variant.label for variant in result.mutation.variants] == ["A", "B"]


async def test_comparison_retries_with_validator_feedback() -> None:
    gateway = RepairingComparisonGateway()
    pipeline = HumorGenomePipeline(gateway)
    result = await pipeline.flow(
        FlowRequest(
            text="I told my therapist I worry about money. She charged me to continue.",
            target_gene=ComedyGene.BREVITY,
        )
    )

    assert gateway.comparison_calls == 2
    assert [observation.label for observation in result.comparison.observations] == ["A", "B"]


async def test_mutation_retries_with_validator_feedback() -> None:
    gateway = RepairingMutationGateway()
    pipeline = HumorGenomePipeline(gateway)
    result = await pipeline.flow(
        FlowRequest(
            text="I told my therapist I worry about money. She charged me to continue.",
            target_gene=ComedyGene.BREVITY,
        )
    )

    assert gateway.mutation_calls == 2
    assert all(variant.changed_gene == ComedyGene.BREVITY for variant in result.mutation.variants)
