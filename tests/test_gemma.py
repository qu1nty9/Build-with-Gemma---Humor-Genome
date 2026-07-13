import httpx
from pydantic import BaseModel

from app.gemma import OllamaGemmaGateway


def test_extract_json_removes_markdown_fence() -> None:
    content = '```json\n{"status": "ok"}\n```'
    assert OllamaGemmaGateway._extract_json(content) == '{"status": "ok"}'


def test_extract_json_removes_leading_commentary() -> None:
    content = 'Here is the result:\n{"status": "ok"}\nDone.'
    assert OllamaGemmaGateway._extract_json(content) == '{"status": "ok"}'


def test_grammar_error_detection_is_narrow() -> None:
    grammar_error = httpx.Response(400, text='{"error":"Failed to initialize samplers: failed to parse grammar"}')
    unrelated_error = httpx.Response(400, text='{"error":"model is missing"}')

    assert OllamaGemmaGateway._is_grammar_error(grammar_error) is True
    assert OllamaGemmaGateway._is_grammar_error(unrelated_error) is False


class EchoEnvelope(BaseModel):
    source_text: str
    target_gene: str
    variants: list[str]


def test_validate_content_restores_authoritative_request_metadata() -> None:
    result = OllamaGemmaGateway._validate_content(
        '{"variants": ["shorter version"]}',
        {"source_text": "source version", "target_gene": "brevity"},
        EchoEnvelope,
    )

    assert result.source_text == "source version"
    assert result.target_gene == "brevity"
    assert result.variants == ["shorter version"]


def test_validate_content_unwraps_exact_schema_name() -> None:
    result = OllamaGemmaGateway._validate_content(
        '{"EchoEnvelope": {"variants": ["shorter version"]}}',
        {"source_text": "source version", "target_gene": "brevity"},
        EchoEnvelope,
    )

    assert result.model_dump() == {
        "source_text": "source version",
        "target_gene": "brevity",
        "variants": ["shorter version"],
    }
