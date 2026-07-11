import httpx

import app.api as api_module
from app.api import app
from app.gemma import GemmaError, GemmaQualityError
from app.pipeline import PipelineQualityError


async def request(method: str, path: str, **kwargs) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path, **kwargs)


async def test_health_endpoint() -> None:
    response = await request("GET", "/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["model"]


async def test_index_serves_the_ui() -> None:
    response = await request("GET", "/")
    assert response.status_code == 200
    assert "Humor Genome Lab" in response.text


async def test_analyze_rejects_empty_text_without_calling_model() -> None:
    response = await request("POST", "/v1/analyze", json={"text": ""})
    assert response.status_code == 422


async def test_model_failure_is_sanitized(monkeypatch) -> None:
    async def fail(_request):
        raise GemmaError("internal runtime detail")

    monkeypatch.setattr(api_module.pipeline, "analyze", fail)
    response = await request("POST", "/v1/analyze", json={"text": "A valid short joke."})
    assert response.status_code == 503
    assert "internal runtime detail" not in response.text
    assert "Gemma is not ready" in response.json()["detail"]


async def test_quality_failure_is_actionable(monkeypatch) -> None:
    async def fail(_request):
        raise PipelineQualityError("variant rewrote the whole premise")

    monkeypatch.setattr(api_module.pipeline, "analyze", fail)
    response = await request("POST", "/v1/analyze", json={"text": "A valid short joke."})
    assert response.status_code == 422
    assert "different gene" in response.json()["detail"]
    assert "whole premise" not in response.text


async def test_gateway_quality_failure_uses_same_actionable_response(monkeypatch) -> None:
    async def fail(_request):
        raise GemmaQualityError("one-gene self-check failed")

    monkeypatch.setattr(api_module.pipeline, "analyze", fail)
    response = await request("POST", "/v1/analyze", json={"text": "A valid short joke."})
    assert response.status_code == 422
    assert "isolate that comedy gene" in response.json()["detail"]
