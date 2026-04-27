"""Tests for OCR engine factories, parser adapters, and registry specs."""

from pathlib import Path

import pytest

from zotron.ocr.engine import (
    CustomEngine,
    GLMEngine,
    OCRResult,
    QwenOCREngine,
    ScaffoldEngine,
    create_engine,
    parse_mineru_response,
    parse_mistral_ocr_response,
    parse_paddleocr_vl_response,
)
from zotron.ocr.registry import get_ocr_engine_spec, list_ocr_engine_specs


def test_create_glm_engine():
    engine = create_engine("glm", api_key="test-key-glm")
    assert isinstance(engine, GLMEngine)
    assert engine.api_key == "test-key-glm"


def test_create_qwen_engine():
    engine = create_engine("qwen", api_key="test-key-qwen")
    assert isinstance(engine, QwenOCREngine)
    assert engine.api_key == "test-key-qwen"


def test_create_custom_engine():
    engine = create_engine(
        "custom",
        api_key="test-key-custom",
        api_url="https://my-llm.example.com/v1/chat/completions",
    )
    assert isinstance(engine, CustomEngine)
    assert engine.api_key == "test-key-custom"
    assert engine.api_url == "https://my-llm.example.com/v1/chat/completions"


def test_create_unknown_engine():
    with pytest.raises(ValueError, match="Unknown OCR provider"):
        create_engine("unknown-provider", api_key="some-key")


def test_engine_requires_api_key():
    with pytest.raises(ValueError, match="api_key must not be None"):
        create_engine("glm", api_key=None)


def test_custom_engine_requires_api_url():
    with pytest.raises(ValueError, match="api_url is required"):
        create_engine("custom", api_key="test-key")


def assert_ocr_result(
    result: OCRResult,
    *,
    provider: str,
    model: str,
    raw_payload: dict,
    content: str,
) -> None:
    assert result.provider == provider
    assert result.model == model
    assert result.raw_payload == raw_payload
    assert result.content == content
    assert result.markdown or result.text
    assert isinstance(result.files, dict)
    assert result.provenance_strength in {"raw", "parsed", "synthetic"}


def test_glm_mock_response_returns_ocr_result():
    payload = {"md_results": "# GLM OCR\n\nbody"}
    result = GLMEngine.parse_response(payload)
    assert_ocr_result(
        result,
        provider="glm",
        model="glm-ocr",
        raw_payload=payload,
        content="# GLM OCR\n\nbody",
    )
    assert result.provenance_strength == "raw"


def test_qwen_mock_response_returns_ocr_result():
    payload = {
        "output": {
            "choices": [{"message": {"content": "Qwen OCR text"}}],
        },
    }
    result = QwenOCREngine.parse_response(payload)
    assert_ocr_result(
        result,
        provider="qwen",
        model="qwen-vl-ocr",
        raw_payload=payload,
        content="Qwen OCR text",
    )


def test_custom_mock_response_returns_ocr_result():
    payload = {"choices": [{"message": {"content": "# Custom markdown"}}]}
    result = CustomEngine.parse_response(payload)
    assert_ocr_result(
        result,
        provider="custom",
        model="vision",
        raw_payload=payload,
        content="# Custom markdown",
    )


def test_scaffold_provider_factories_are_registered_and_mockable():
    for provider in ("mineru", "paddleocr-vl", "mistral-ocr"):
        engine = create_engine(provider, api_key="test-key")
        assert isinstance(engine, ScaffoldEngine)
        assert engine.provider == provider
        with pytest.raises(NotImplementedError, match=provider):
            engine.ocr_pdf(Path("paper.pdf"))


def test_scaffold_parser_functions_return_ocr_results_with_raw_payload_and_files():
    mineru_payload = {"markdown": "# MinerU", "files": {"layout.json": "{}"}}
    paddle_payload = {"text": "Paddle text"}
    mistral_payload = {"pages": [{"markdown": "# Page 1"}, {"markdown": "Page 2"}]}

    mineru = parse_mineru_response(mineru_payload)
    paddle = parse_paddleocr_vl_response(paddle_payload)
    mistral = parse_mistral_ocr_response(mistral_payload)

    assert_ocr_result(mineru, provider="mineru", model="mineru", raw_payload=mineru_payload, content="# MinerU")
    assert mineru.files == {"layout.json": "{}"}
    assert_ocr_result(paddle, provider="paddleocr-vl", model="paddleocr-vl", raw_payload=paddle_payload, content="Paddle text")
    assert_ocr_result(mistral, provider="mistral-ocr", model="mistral-ocr", raw_payload=mistral_payload, content="# Page 1\n\nPage 2")


def test_registry_exposes_roadmap_provider_specs():
    specs = {spec.id: spec for spec in list_ocr_engine_specs()}
    for provider in (
        "glm",
        "qwen",
        "custom",
        "openai-vision-compat",
        "olmocr",
        "mistral-ocr",
        "mineru",
        "paddleocr-vl",
        "mathpix",
        "doubao-ocr",
    ):
        assert provider in specs

    assert get_ocr_engine_spec("glm").request_style == "glm-layout-parsing"
    with pytest.raises(ValueError, match="Unknown OCR provider"):
        get_ocr_engine_spec("unknown")
