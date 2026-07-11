from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.feedback import FeedbackStore
from app.gemma import GemmaError, GemmaQualityError, OllamaGemmaGateway
from app.pipeline import HumorGenomePipeline, PipelineQualityError
from app.schemas import (
    AnalyzeRequest,
    CompareRequest,
    ComparisonResponse,
    FlowRequest,
    FlowResponse,
    FeedbackReceipt,
    FeedbackRequest,
    HumorGenome,
    MutationRequest,
    MutationResponse,
)

app = FastAPI(title="Humor Genome Lab", version="0.1.0")
pipeline = HumorGenomePipeline(OllamaGemmaGateway(settings))
feedback_store = FeedbackStore(settings.feedback_db_path)
static_dir = Path(__file__).parent / "static"
logger = logging.getLogger(__name__)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "model": settings.gemma_model}


async def _run(operation):
    try:
        return await operation
    except (GemmaQualityError, PipelineQualityError) as exc:
        logger.info("Controlled mutation failed quality gates: %s", exc)
        raise HTTPException(
            status_code=422,
            detail="Gemma could not isolate that comedy gene reliably. Try a different gene or revise the source material.",
        ) from exc
    except GemmaError as exc:
        logger.warning("Gemma operation failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Gemma is not ready for this run yet. Check that the configured model is installed and try again.",
        ) from exc


@app.post("/v1/analyze", response_model=HumorGenome)
async def analyze(request: AnalyzeRequest) -> HumorGenome:
    return await _run(pipeline.analyze(request))


@app.post("/v1/mutate", response_model=MutationResponse)
async def mutate(request: MutationRequest) -> MutationResponse:
    return await _run(pipeline.mutate(request))


@app.post("/v1/compare", response_model=ComparisonResponse)
async def compare(request: CompareRequest) -> ComparisonResponse:
    return await _run(pipeline.compare(request))


@app.post("/v1/flow", response_model=FlowResponse)
async def flow(request: FlowRequest) -> FlowResponse:
    return await _run(pipeline.flow(request))


@app.post("/v1/feedback", response_model=FeedbackReceipt)
async def save_feedback(request: FeedbackRequest) -> FeedbackReceipt:
    return feedback_store.save(request)
