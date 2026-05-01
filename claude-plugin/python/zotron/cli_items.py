"""CLI: items namespace."""
from __future__ import annotations

import json

import typer

from zotron._cli_base import DEFAULT_URL, new_rpc, die, rpc_or_die, dry_run, emit_or_die, resolve_or_die

items_app = typer.Typer(
    help="Add items by DOI/ISBN/URL; inspect; trash; find/merge duplicates.",
    no_args_is_help=True,
)


@items_app.command(
    "get",
    epilog="Examples:\n\n    zotron items get 12345",
)
def items_get(
    item_id: int = typer.Argument(...),
    url: str = typer.Option(DEFAULT_URL, "--url"),
    output: str = typer.Option("json", "--output", "-o",
        help="Output format: json (default) or table."),
    jq_filter: str | None = typer.Option(None, "--jq", help="jq filter expression"),
) -> None:
    """Print the full serialization of an item by id."""
    emit_or_die(rpc_or_die(new_rpc(url), "items.get", {"id": item_id}),
                 output=output, jq_filter=jq_filter)


@items_app.command(
    "add-by-doi",
    epilog='Examples:\n\n    zotron items add-by-doi 10.1038/nature12373\n\n    zotron items add-by-doi 10.1038/nature12373 --collection "2026-AI"',
)
def items_add_by_doi(
    doi: str = typer.Argument(...),
    collection: str | None = typer.Option(None, "--collection"),
    url: str = typer.Option(DEFAULT_URL, "--url"),
    dry_run_flag: bool = typer.Option(False, "--dry-run",
        help="Print intended RPC call as JSON; do not execute."),
) -> None:
    """Add a paper by DOI (uses Zotero's search translators)."""
    rpc = new_rpc(url)
    params: dict = {"doi": doi}
    if collection is not None:
        coll_id = resolve_or_die(rpc, collection) or None
        if coll_id and coll_id != 0:
            params["collection"] = coll_id
    if dry_run_flag:
        dry_run("items.addByDOI", params)
    typer.echo(json.dumps(rpc_or_die(rpc, "items.addByDOI", params)))


@items_app.command(
    "add-by-isbn",
    epilog="Examples:\n\n    zotron items add-by-isbn 9780262035613",
)
def items_add_by_isbn(
    isbn: str = typer.Argument(...),
    collection: str | None = typer.Option(None, "--collection"),
    url: str = typer.Option(DEFAULT_URL, "--url"),
    dry_run_flag: bool = typer.Option(False, "--dry-run",
        help="Print intended RPC call as JSON; do not execute."),
) -> None:
    """Add a book by ISBN."""
    rpc = new_rpc(url)
    params: dict = {"isbn": isbn}
    if collection is not None:
        coll_id = resolve_or_die(rpc, collection) or None
        if coll_id and coll_id != 0:
            params["collection"] = coll_id
    if dry_run_flag:
        dry_run("items.addByISBN", params)
    typer.echo(json.dumps(rpc_or_die(rpc, "items.addByISBN", params)))


@items_app.command(
    "add-by-url",
    epilog="Examples:\n\n    zotron items add-by-url https://arxiv.org/abs/1706.03762",
)
def items_add_by_url(
    page_url: str = typer.Argument(...),
    collection: str | None = typer.Option(None, "--collection"),
    url: str = typer.Option(DEFAULT_URL, "--url"),
    dry_run_flag: bool = typer.Option(False, "--dry-run",
        help="Print intended RPC call as JSON; do not execute."),
) -> None:
    """Add a web resource via Zotero's web translator."""
    rpc = new_rpc(url)
    params: dict = {"url": page_url}
    if collection is not None:
        coll_id = resolve_or_die(rpc, collection) or None
        if coll_id and coll_id != 0:
            params["collection"] = coll_id
    if dry_run_flag:
        dry_run("items.addByURL", params)
    typer.echo(json.dumps(rpc_or_die(rpc, "items.addByURL", params)))


@items_app.command(
    "trash",
    epilog="Examples:\n\n    zotron items trash 12345",
)
def items_trash(
    item_id: int = typer.Argument(...),
    url: str = typer.Option(DEFAULT_URL, "--url"),
    dry_run_flag: bool = typer.Option(False, "--dry-run",
        help="Print intended RPC call as JSON; do not execute."),
) -> None:
    """Move item to trash (reversible via `restore`)."""
    if dry_run_flag:
        dry_run("items.trash", {"id": item_id})
    typer.echo(json.dumps(rpc_or_die(new_rpc(url), "items.trash",
                                      {"id": item_id})))


@items_app.command(
    "restore",
    epilog="Examples:\n\n    zotron items restore 12345",
)
def items_restore(
    item_id: int = typer.Argument(...),
    url: str = typer.Option(DEFAULT_URL, "--url"),
    dry_run_flag: bool = typer.Option(False, "--dry-run",
        help="Print intended RPC call as JSON; do not execute."),
) -> None:
    """Restore a trashed item."""
    if dry_run_flag:
        dry_run("items.restore", {"id": item_id})
    typer.echo(json.dumps(rpc_or_die(new_rpc(url), "items.restore",
                                      {"id": item_id})))


@items_app.command(
    "find-duplicates",
    epilog="Examples:\n\n    zotron items find-duplicates",
)
def items_find_duplicates(
    url: str = typer.Option(DEFAULT_URL, "--url"),
    jq_filter: str | None = typer.Option(None, "--jq", help="jq filter expression"),
) -> None:
    """Run Zotero's duplicate scan and print groups."""
    emit_or_die(rpc_or_die(new_rpc(url), "items.findDuplicates"),
                 jq_filter=jq_filter)


@items_app.command(
    "merge-duplicates",
    epilog="Examples:\n\n    zotron items merge-duplicates 12345 12346 12347",
)
def items_merge_duplicates(
    ids: list[int] = typer.Argument(..., help="First id is the master; rest merged into it."),
    url: str = typer.Option(DEFAULT_URL, "--url"),
    dry_run_flag: bool = typer.Option(False, "--dry-run",
        help="Print intended RPC call as JSON; do not execute."),
) -> None:
    """Merge a group of duplicate items. Takes >= 2 ids."""
    if len(ids) < 2:
        die("INVALID_ARGS", "need at least 2 ids to merge", 2)
    if dry_run_flag:
        dry_run("items.mergeDuplicates", {"ids": ids})
    typer.echo(json.dumps(rpc_or_die(new_rpc(url), "items.mergeDuplicates",
                                      {"ids": ids})))
