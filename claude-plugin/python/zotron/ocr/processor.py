"""OCR processor: orchestrates collection traversal, OCR, and Note creation."""

from __future__ import annotations

import datetime
from pathlib import Path

import markdown as md

from zotron.collections import find_by_name as _find_collection_by_name
from zotron.ocr.engine import OCREngine
from zotron.rpc import ZoteroRPC


class OCRProcessor:
    """Orchestrates: find collection → iterate items → OCR → write Note."""

    def __init__(self, rpc: ZoteroRPC, engine: OCREngine) -> None:
        self.rpc = rpc
        self.engine = engine

    # ------------------------------------------------------------------
    # Collection helpers
    # ------------------------------------------------------------------

    def find_collection_id(self, name: str) -> int | None:
        """Search the collections tree recursively for a collection by name."""
        return _find_collection_by_name(self.rpc, name)

    # ------------------------------------------------------------------
    # Note helpers
    # ------------------------------------------------------------------

    def has_ocr_note(self, item_id: int) -> bool:
        """Return True if the item already has a Note tagged 'ocr'."""
        notes = self.rpc.call("notes.get", {"parentId": item_id}) or []
        for note in notes:
            tags = note.get("tags") or []
            if "ocr" in tags:
                return True
        return False

    # ------------------------------------------------------------------
    # Attachment helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_linux_path(win_path: str) -> str:
        """Convert a Windows path to a WSL Linux path if running under WSL."""
        import subprocess
        try:
            r = subprocess.run(
                ["wslpath", "-u", win_path],
                capture_output=True, text=True, timeout=5,
            )
            if r.returncode == 0:
                return r.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return win_path

    def get_pdf_path(self, item_id: int) -> Path | None:
        """Return the filesystem path to the first PDF attachment, or None."""
        attachments = self.rpc.call("attachments.list", {"parentId": item_id}) or []
        for att in attachments:
            if att.get("contentType") == "application/pdf":
                att_id = att.get("id")
                result = self.rpc.call("attachments.getPath", {"id": att_id})
                path_str = result.get("path") if isinstance(result, dict) else result
                if path_str:
                    # Zotero returns Windows paths; convert for WSL
                    linux_path = self._to_linux_path(path_str)
                    return Path(linux_path)
        return None

    # ------------------------------------------------------------------
    # HTML formatting
    # ------------------------------------------------------------------

    def format_note_html(
        self,
        title: str,
        markdown: str,
        provider: str,
        page_count: int | None = None,
    ) -> str:
        """Convert markdown to HTML and wrap with OCR header.

        Parameters
        ----------
        title:
            Title of the source item.
        markdown:
            OCR output in Markdown format.
        provider:
            Name of the OCR engine/provider.
        page_count:
            Optional page count to include in the header.

        Returns
        -------
        str
            HTML string suitable for use as a Zotero note body.
        """
        date_str = datetime.date.today().isoformat()
        if page_count is not None:
            meta = f"OCR by {provider} | {date_str} | {page_count} pages"
        else:
            meta = f"OCR by {provider} | {date_str}"

        body_html = md.markdown(
            markdown, extensions=["tables", "fenced_code"]
        )

        return (
            f"<h1>OCR: {title}</h1>\n"
            f"<p><em>{meta}</em></p>\n"
            f"<hr/>\n"
            f"{body_html}"
        )

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def process_item(
        self, item_id: int, title: str, force: bool = False
    ) -> str:
        """OCR a single item and write a Note back to Zotero.

        Parameters
        ----------
        item_id:
            Zotero item id.
        title:
            Item title (used in the Note header).
        force:
            If True, re-OCR even if an OCR note already exists.

        Returns
        -------
        str
            ``"ok"``, ``"skipped"``, or ``"error: <message>"``.
        """
        try:
            if not force and self.has_ocr_note(item_id):
                return "skipped"

            pdf_path = self.get_pdf_path(item_id)
            if pdf_path is None:
                return "error: no PDF attachment found"

            ocr_text = self.engine.ocr_pdf(pdf_path)
            provider = type(self.engine).__name__

            html = self.format_note_html(title, ocr_text, provider)

            self.rpc.call(
                "notes.create",
                {
                    "parentId": item_id,
                    "content": html,
                    "tags": ["ocr"],
                },
            )
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def process_collection(
        self, collection_name: str, force: bool = False
    ) -> dict:
        """OCR all items in the named collection.

        Parameters
        ----------
        collection_name:
            Name of the Zotero collection to process.
        force:
            Passed through to :meth:`process_item`.

        Returns
        -------
        dict
            ``{"ok": N, "skipped": M, "errors": [...]}``.
        """
        result: dict = {"ok": 0, "skipped": 0, "errors": []}

        collection_id = self.find_collection_id(collection_name)
        if collection_id is None:
            result["errors"].append(
                f"Collection not found: {collection_name!r}"
            )
            return result

        raw = self.rpc.call("collections.getItems", {"id": collection_id, "limit": 500}) or {}
        items = raw.get("items", []) if isinstance(raw, dict) else raw

        for item in items:
            item_id = item.get("id")
            title = item.get("title", "(untitled)")
            status = self.process_item(item_id, title, force=force)
            if status == "ok":
                result["ok"] += 1
            elif status == "skipped":
                result["skipped"] += 1
            else:
                result["errors"].append(f"[{item_id}] {title}: {status}")

        return result
