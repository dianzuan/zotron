"""CLI entry point for zotron-ocr command."""

from __future__ import annotations

import argparse
import json
import sys

from zotron.config import load_config
from zotron.rpc import ZoteroRPC
from zotron.ocr.engine import create_engine
from zotron.ocr.processor import OCRProcessor


def _make_processor(cfg: dict) -> OCRProcessor:
    rpc = ZoteroRPC(url=cfg["zotero"]["rpc_url"])
    engine = create_engine(
        provider=cfg["ocr"]["provider"],
        api_key=cfg["ocr"].get("api_key") or cfg["ocr"].get("glm_api_key") or None,
        api_url=cfg["ocr"].get("api_url"),
    )
    return OCRProcessor(rpc=rpc, engine=engine)


def cmd_status(args: argparse.Namespace, cfg: dict) -> None:
    """Show OCR stats for a collection (JSON to stdout)."""
    proc = _make_processor(cfg)
    collection_id = proc.find_collection_id(args.collection)
    if collection_id is None:
        result = {"error": f"Collection not found: {args.collection!r}"}
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    raw = proc.rpc.call("collections.getItems", {"id": collection_id, "limit": 500}) or {}
    items = raw.get("items", []) if isinstance(raw, dict) else raw
    total = len(items)
    has_ocr = sum(1 for item in items if proc.has_ocr_note(item.get("id")))
    result = {
        "collection": args.collection,
        "total": total,
        "has_ocr": has_ocr,
        "missing_ocr": total - has_ocr,
    }
    print(json.dumps(result, ensure_ascii=False))


def cmd_process(args: argparse.Namespace, cfg: dict) -> None:
    """Process a collection or single item (JSON result to stdout)."""
    proc = _make_processor(cfg)

    if args.item is not None:
        # Single item mode
        item_id = args.item
        try:
            item_info = proc.rpc.call("items.get", {"id": item_id}) or {}
            title = item_info.get("title", "(untitled)")
        except Exception:
            title = "(untitled)"
        status = proc.process_item(item_id, title, force=args.force)
        result = {"item_id": item_id, "status": status}
    elif args.collection is not None:
        result = proc.process_collection(args.collection, force=args.force)
    else:
        print(
            json.dumps({"error": "Specify --collection or --item"}),
            file=sys.stderr,
        )
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="zotron-ocr",
        description="OCR PDFs in Zotero and write results as Notes.",
    )
    parser.add_argument("--collection", help="Collection name to process")
    parser.add_argument("--item", type=int, help="Single item ID to process")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-OCR even if an OCR Note already exists",
    )

    sub = parser.add_subparsers(dest="command")
    status_p = sub.add_parser("status", help="Show OCR statistics for a collection")
    status_p.add_argument(
        "--collection", required=True, help="Collection name"
    )

    args = parser.parse_args()
    cfg = load_config()

    try:
        if args.command == "status":
            cmd_status(args, cfg)
        else:
            cmd_process(args, cfg)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
