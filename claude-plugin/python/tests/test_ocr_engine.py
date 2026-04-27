"""Tests for the OCR engine factory and construction (no HTTP calls)."""

import pytest

from zotron.ocr.engine import (
    CustomEngine,
    GLMEngine,
    QwenOCREngine,
    create_engine,
)


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
