"""OCR engine abstraction: GLM-OCR, Qwen-VL-OCR, and Custom."""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from pathlib import Path

import httpx

_TIMEOUT = 120.0


class OCREngine(ABC):
    """Abstract base class for OCR engines."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @abstractmethod
    def ocr_pdf(self, pdf_path: Path) -> str:
        """Convert a PDF file to Markdown text."""

    def _read_pdf_b64(self, pdf_path: Path) -> str:
        return base64.b64encode(pdf_path.read_bytes()).decode("ascii")

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}


class GLMEngine(OCREngine):
    """智谱 GLM-OCR — dedicated OCR model via /v4/layout_parsing endpoint."""

    _API_URL = "https://open.bigmodel.cn/api/paas/v4/layout_parsing"

    def ocr_pdf(self, pdf_path: Path) -> str:
        pdf_b64 = self._read_pdf_b64(pdf_path)
        payload = {
            "model": "glm-ocr",
            "file": f"data:application/pdf;base64,{pdf_b64}",
        }
        response = httpx.post(
            self._API_URL,
            json=payload,
            headers=self._auth_headers(),
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        # GLM-OCR layout_parsing returns md_results (Markdown)
        if "md_results" in data:
            return data["md_results"]
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        if "result" in data:
            return data["result"]
        return str(data)


class QwenOCREngine(OCREngine):
    """阿里通义千问 Qwen-VL-OCR — DashScope native endpoint."""

    _API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

    def ocr_pdf(self, pdf_path: Path) -> str:
        pdf_b64 = self._read_pdf_b64(pdf_path)
        payload = {
            "model": "qwen-vl-ocr",
            "input": {
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "image": f"data:application/pdf;base64,{pdf_b64}",
                            "min_pixels": 3072,
                            "max_pixels": 8388608,
                        },
                        {"text": "Read all the text in the image."},
                    ],
                }],
            },
        }
        response = httpx.post(
            self._API_URL,
            json=payload,
            headers=self._auth_headers(),
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data["output"]["choices"][0]["message"]["content"]


class CustomEngine(OCREngine):
    """Custom OCR endpoint — OpenAI vision API compatible."""

    def __init__(self, api_key: str, api_url: str) -> None:
        super().__init__(api_key)
        self.api_url = api_url

    def ocr_pdf(self, pdf_path: Path) -> str:
        pdf_b64 = self._read_pdf_b64(pdf_path)
        payload = {
            "model": "vision",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:application/pdf;base64,{pdf_b64}"}},
                    {"type": "text", "text": "Convert this PDF to Markdown. Preserve headings, tables, equations."},
                ],
            }],
        }
        response = httpx.post(
            self.api_url,
            json=payload,
            headers=self._auth_headers(),
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def create_engine(
    provider: str,
    api_key: str | None,
    api_url: str | None = None,
) -> OCREngine:
    """Factory: create OCR engine by provider name."""
    if api_key is None:
        raise ValueError("api_key must not be None")

    match provider:
        case "glm":
            return GLMEngine(api_key=api_key)
        case "qwen":
            return QwenOCREngine(api_key=api_key)
        case "custom":
            if api_url is None:
                raise ValueError("api_url is required for the 'custom' provider")
            return CustomEngine(api_key=api_key, api_url=api_url)
        case _:
            raise ValueError(f"Unknown OCR provider: {provider!r}")
