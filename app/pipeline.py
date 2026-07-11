from __future__ import annotations

import time

from app.gemma import ModelGateway
from app.schemas import (
    AnalyzeRequest,
    CompareRequest,
    ComparisonResponse,
    FlowRequest,
    FlowResponse,
    HumorGenome,
    MutationRequest,
    MutationResponse,
)
from app.validation import comparison_issues, mutation_issues


class PipelineQualityError(RuntimeError):
    """Raised when structured output passes schema validation but fails deterministic quality gates."""


class HumorGenomePipeline:
    def __init__(self, gateway: ModelGateway) -> None:
        self.gateway = gateway

    async def analyze(self, request: AnalyzeRequest) -> HumorGenome:
        return await self.gateway.generate(
            prompt_name="analyze_v1",
            user_payload=request.model_dump(mode="json"),
            schema=HumorGenome,
        )

    @staticmethod
    def _normalize_mutation_response(
        request: MutationRequest,
        response: MutationResponse,
    ) -> MutationResponse:
        return response.model_copy(
            update={
                "source_text": request.source_text,
                "target_gene": request.target_gene,
                "variants": response.variants[: request.number_of_variants],
            }
        )

    async def mutate(self, request: MutationRequest) -> MutationResponse:
        response = await self.gateway.generate(
            prompt_name="mutate_v1",
            user_payload=request.model_dump(mode="json"),
            schema=MutationResponse,
        )
        response = self._normalize_mutation_response(request, response)
        issues = mutation_issues(request, response)
        if not issues:
            return response

        retry_payload = request.model_dump(mode="json")
        retry_payload["validator_feedback"] = issues
        retry_payload["instruction"] = "Regenerate all variants and fix every validator issue."
        repaired = await self.gateway.generate(
            prompt_name="mutate_v1",
            user_payload=retry_payload,
            schema=MutationResponse,
        )
        repaired = self._normalize_mutation_response(request, repaired)
        remaining_issues = mutation_issues(request, repaired)
        if remaining_issues:
            raise PipelineQualityError("; ".join(remaining_issues))
        return repaired

    async def compare(self, request: CompareRequest) -> ComparisonResponse:
        response = await self.gateway.generate(
            prompt_name="compare_v1",
            user_payload=request.model_dump(mode="json"),
            schema=ComparisonResponse,
        )
        issues = comparison_issues(request, response)
        if not issues:
            return response

        retry_payload = request.model_dump(mode="json")
        retry_payload["validator_feedback"] = issues
        retry_payload["instruction"] = "Regenerate the comparison and fix every validator issue."
        repaired = await self.gateway.generate(
            prompt_name="compare_v1",
            user_payload=retry_payload,
            schema=ComparisonResponse,
        )
        remaining_issues = comparison_issues(request, repaired)
        if remaining_issues:
            raise PipelineQualityError("; ".join(remaining_issues))
        return repaired

    async def flow(self, request: FlowRequest) -> FlowResponse:
        stage_latency: dict[str, float] = {}
        started = time.perf_counter()
        genome = await self.analyze(AnalyzeRequest(text=request.text, context=request.context))
        stage_latency["analyze"] = round(time.perf_counter() - started, 3)

        started = time.perf_counter()
        mutation = await self.mutate(
            MutationRequest(
                source_text=request.text,
                genome=genome,
                target_gene=request.target_gene,
                context=request.context,
                number_of_variants=request.number_of_variants,
            )
        )
        stage_latency["mutate"] = round(time.perf_counter() - started, 3)

        started = time.perf_counter()
        comparison = await self.compare(
            CompareRequest(
                source_text=request.text,
                variants=mutation.variants,
                context=request.context,
            )
        )
        stage_latency["compare"] = round(time.perf_counter() - started, 3)
        return FlowResponse(
            genome=genome,
            mutation=mutation,
            comparison=comparison,
            model=self.gateway.model_name,
            stage_latency_seconds=stage_latency,
        )
