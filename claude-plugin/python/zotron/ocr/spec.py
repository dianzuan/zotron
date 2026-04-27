"""OCR provider specification model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RequestStyle = Literal[
    "glm-layout-parsing",
    "dashscope-multimodal",
    "openai-vision",
    "olmocr-vllm",
    "mistral-ocr",
    "mineru-cli",
    "mathpix",
]
AuthStyle = Literal["bearer", "header-key", "none"]


@dataclass(frozen=True)
class OCREngineSpec:
    """Static capabilities and transport hints for an OCR provider."""

    id: str
    request_style: RequestStyle
    base_url: str | None
    auth: AuthStyle
    auth_header: str = "Authorization"
    auth_prefix: str = "Bearer "
    supports_pdf_direct: bool = True
    max_pages_per_request: int | None = None
    cost_per_page_usd: float | None = None
    notes: str = ""
