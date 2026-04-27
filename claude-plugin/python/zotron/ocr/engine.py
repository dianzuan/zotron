"""OCR engine abstraction and provider registry-backed adapters."""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

import httpx

_TIMEOUT = 120.0
ProvenanceStrength = Literal["raw", "parsed", "synthetic"]


@dataclass(frozen=True)
class OCRResult:
    """Normalized OCR adapter result with auditable provider evidence."""

    provider: str
    model: str
    raw_payload: Any
    markdown: str | None = None
    text: str | None = None
    files: dict[str, bytes | str] = field(default_factory=dict)
    provenance_strength: ProvenanceStrength = "parsed"

    @property
    def content(self) -> str:
        """Return the best available human-readable OCR content."""
        return self.markdown or self.text or ""

    def __str__(self) -> str:
        """Preserve old string-like behavior for callers that coerce results."""
        return self.content


Parser = Callable[[Any], OCRResult]


class OCREngine(ABC):
    """Abstract base class for OCR engines."""

    provider = "unknown"
    model = "unknown"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @abstractmethod
    def ocr_pdf(self, pdf_path: Path) -> OCRResult:
        """Convert a PDF file to an OCR result with raw provider evidence."""

    def _read_pdf_b64(self, pdf_path: Path) -> str:
        return base64.b64encode(pdf_path.read_bytes()).decode("ascii")

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}


class GLMEngine(OCREngine):
    """智谱 GLM-OCR — dedicated OCR model via /v4/layout_parsing endpoint."""

    provider = "glm"
    model = "glm-ocr"
    _API_URL = "https://open.bigmodel.cn/api/paas/v4/layout_parsing"

    @staticmethod
    def parse_response(data: Any) -> OCRResult:
        """Parse GLM layout_parsing response into an OCRResult."""
        markdown: str | None = None
        text: str | None = None
        if isinstance(data, dict):
            if "md_results" in data:
                markdown = str(data["md_results"])
            elif "choices" in data:
                text = str(data["choices"][0]["message"]["content"])
            elif "result" in data:
                markdown = str(data["result"])
        return OCRResult(
            provider=GLMEngine.provider,
            model=GLMEngine.model,
            raw_payload=data,
            markdown=markdown,
            text=text if markdown is None else None,
            provenance_strength="raw" if markdown is not None else "parsed",
        )

    def ocr_pdf(self, pdf_path: Path) -> OCRResult:
        pdf_b64 = self._read_pdf_b64(pdf_path)
        payload = {
            "model": self.model,
            "file": f"data:application/pdf;base64,{pdf_b64}",
        }
        response = httpx.post(
            self._API_URL,
            json=payload,
            headers=self._auth_headers(),
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return self.parse_response(response.json())


class QwenOCREngine(OCREngine):
    """阿里通义千问 Qwen-VL-OCR — DashScope native endpoint."""

    provider = "qwen"
    model = "qwen-vl-ocr"
    _API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

    @staticmethod
    def parse_response(data: Any) -> OCRResult:
        """Parse DashScope multimodal response into an OCRResult."""
        text: str | None = None
        if isinstance(data, dict):
            text = str(data["output"]["choices"][0]["message"]["content"])
        return OCRResult(
            provider=QwenOCREngine.provider,
            model=QwenOCREngine.model,
            raw_payload=data,
            text=text,
            provenance_strength="parsed",
        )

    def ocr_pdf(self, pdf_path: Path) -> OCRResult:
        pdf_b64 = self._read_pdf_b64(pdf_path)
        payload = {
            "model": self.model,
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
        return self.parse_response(response.json())


class CustomEngine(OCREngine):
    """Custom OCR endpoint — OpenAI vision API compatible."""

    provider = "custom"
    model = "vision"

    def __init__(self, api_key: str, api_url: str) -> None:
        super().__init__(api_key)
        self.api_url = api_url

    @staticmethod
    def parse_response(data: Any) -> OCRResult:
        """Parse OpenAI-compatible chat completion response into an OCRResult."""
        text: str | None = None
        if isinstance(data, dict):
            text = str(data["choices"][0]["message"]["content"])
        return OCRResult(
            provider=CustomEngine.provider,
            model=CustomEngine.model,
            raw_payload=data,
            markdown=text,
            provenance_strength="parsed",
        )

    def ocr_pdf(self, pdf_path: Path) -> OCRResult:
        pdf_b64 = self._read_pdf_b64(pdf_path)
        payload = {
            "model": self.model,
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
        return self.parse_response(response.json())


class ScaffoldEngine(OCREngine):
    """Roadmap adapter scaffold with mockable parser functions."""

    def __init__(self, api_key: str, provider: str, model: str, parser: Parser) -> None:
        super().__init__(api_key)
        self.provider = provider
        self.model = model
        self._parser = parser

    def parse_response(self, data: Any) -> OCRResult:
        return self._parser(data)

    def ocr_pdf(self, pdf_path: Path) -> OCRResult:
        raise NotImplementedError(
            f"OCR provider {self.provider!r} is registered as a parser scaffold; "
            "wire its transport before live OCR use."
        )


def _first_string(data: Any, keys: tuple[str, ...]) -> str | None:
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def parse_mineru_response(data: Any) -> OCRResult:
    markdown = _first_string(data, ("markdown", "md", "content"))
    files = data.get("files", {}) if isinstance(data, dict) and isinstance(data.get("files"), dict) else {}
    return OCRResult("mineru", "mineru", data, markdown=markdown, files=files, provenance_strength="parsed")


def parse_paddleocr_vl_response(data: Any) -> OCRResult:
    markdown = _first_string(data, ("markdown", "md"))
    text = _first_string(data, ("text", "content"))
    return OCRResult("paddleocr-vl", "paddleocr-vl", data, markdown=markdown, text=text, provenance_strength="parsed")


def parse_mistral_ocr_response(data: Any) -> OCRResult:
    markdown = _first_string(data, ("markdown", "content"))
    if markdown is None and isinstance(data, dict) and isinstance(data.get("pages"), list):
        page_markdown = [str(page.get("markdown", "")) for page in data["pages"] if isinstance(page, dict)]
        markdown = "\n\n".join(part for part in page_markdown if part)
    return OCRResult("mistral-ocr", "mistral-ocr", data, markdown=markdown, provenance_strength="parsed")


_ENGINE_FACTORIES = {
    "glm": lambda api_key, api_url=None: GLMEngine(api_key=api_key),
    "qwen": lambda api_key, api_url=None: QwenOCREngine(api_key=api_key),
    "custom": lambda api_key, api_url=None: CustomEngine(api_key=api_key, api_url=_require_api_url(api_url)),
    "mineru": lambda api_key, api_url=None: ScaffoldEngine(api_key, "mineru", "mineru", parse_mineru_response),
    "paddleocr-vl": lambda api_key, api_url=None: ScaffoldEngine(api_key, "paddleocr-vl", "paddleocr-vl", parse_paddleocr_vl_response),
    "mistral-ocr": lambda api_key, api_url=None: ScaffoldEngine(api_key, "mistral-ocr", "mistral-ocr", parse_mistral_ocr_response),
}


def _require_api_url(api_url: str | None) -> str:
    if api_url is None:
        raise ValueError("api_url is required for the 'custom' provider")
    return api_url


def create_engine(provider: str, api_key: str | None, api_url: str | None = None) -> OCREngine:
    """Factory: create OCR engine by provider name."""
    if api_key is None:
        raise ValueError("api_key must not be None")

    try:
        factory = _ENGINE_FACTORIES[provider]
    except KeyError as exc:
        raise ValueError(f"Unknown OCR provider: {provider!r}") from exc
    return factory(api_key, api_url)
