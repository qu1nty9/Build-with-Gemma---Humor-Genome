from app.gemma import OllamaGemmaGateway


def test_extract_json_removes_markdown_fence() -> None:
    content = '```json\n{"status": "ok"}\n```'
    assert OllamaGemmaGateway._extract_json(content) == '{"status": "ok"}'


def test_extract_json_removes_leading_commentary() -> None:
    content = 'Here is the result:\n{"status": "ok"}\nDone.'
    assert OllamaGemmaGateway._extract_json(content) == '{"status": "ok"}'

