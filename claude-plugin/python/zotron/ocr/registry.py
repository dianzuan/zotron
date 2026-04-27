"""Built-in OCR provider registry."""

from __future__ import annotations

from zotron.ocr.spec import OCREngineSpec

BUILTIN_OCR_ENGINE_SPECS: dict[str, OCREngineSpec] = {
    "glm": OCREngineSpec(
        id="glm",
        request_style="glm-layout-parsing",
        base_url="https://open.bigmodel.cn/api/paas/v4/layout_parsing",
        auth="bearer",
        notes="Zhipu GLM layout parsing OCR endpoint.",
    ),
    "qwen": OCREngineSpec(
        id="qwen",
        request_style="dashscope-multimodal",
        base_url="https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
        auth="bearer",
        notes="DashScope Qwen-VL OCR-compatible multimodal endpoint.",
    ),
    "custom": OCREngineSpec(
        id="custom",
        request_style="openai-vision",
        base_url=None,
        auth="bearer",
        notes="User-supplied OpenAI vision-compatible endpoint.",
    ),
    "openai-vision-compat": OCREngineSpec(
        id="openai-vision-compat",
        request_style="openai-vision",
        base_url=None,
        auth="bearer",
        notes="Generic OpenAI-compatible vision endpoint preset.",
    ),
    "olmocr": OCREngineSpec(
        id="olmocr",
        request_style="olmocr-vllm",
        base_url=None,
        auth="bearer",
        notes="vLLM-hosted olmOCR endpoint; configure base_url locally.",
    ),
    "mistral-ocr": OCREngineSpec(
        id="mistral-ocr",
        request_style="mistral-ocr",
        base_url="https://api.mistral.ai/v1/ocr",
        auth="bearer",
        notes="Mistral OCR API parser scaffold.",
    ),
    "mineru": OCREngineSpec(
        id="mineru",
        request_style="mineru-cli",
        base_url=None,
        auth="none",
        notes="Local MinerU CLI parser scaffold.",
    ),
    "paddleocr-vl": OCREngineSpec(
        id="paddleocr-vl",
        request_style="openai-vision",
        base_url=None,
        auth="bearer",
        notes="PaddleOCR-VL service parser scaffold.",
    ),
    "mathpix": OCREngineSpec(
        id="mathpix",
        request_style="mathpix",
        base_url="https://api.mathpix.com/v3/pdf",
        auth="header-key",
        auth_prefix="",
        notes="Mathpix PDF OCR endpoint preset.",
    ),
    "doubao-ocr": OCREngineSpec(
        id="doubao-ocr",
        request_style="openai-vision",
        base_url=None,
        auth="bearer",
        notes="Doubao/OpenAI-compatible vision OCR preset.",
    ),
}


def get_ocr_engine_spec(provider: str) -> OCREngineSpec:
    """Return the built-in provider spec or raise a clear provider error."""
    try:
        return BUILTIN_OCR_ENGINE_SPECS[provider]
    except KeyError as exc:
        raise ValueError(f"Unknown OCR provider: {provider!r}") from exc


def list_ocr_engine_specs() -> list[OCREngineSpec]:
    """Return built-in provider specs in deterministic order."""
    return [BUILTIN_OCR_ENGINE_SPECS[key] for key in sorted(BUILTIN_OCR_ENGINE_SPECS)]
