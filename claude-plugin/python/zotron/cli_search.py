"""CLI: search namespace."""
from __future__ import annotations

import json

import typer

from zotron._cli_base import DEFAULT_URL, new_rpc, die, rpc_or_die, emit_or_die

search_app = typer.Typer(
    help="Search items by text / tag / identifier.",
    no_args_is_help=True,
)


@search_app.command(
    "quick",
    epilog='Examples:\n\n    zotron search quick "transformer" --limit 10',
)
def search_quick(
    query: str = typer.Argument(...),
    limit: int = typer.Option(50, "--limit"),
    url: str = typer.Option(DEFAULT_URL, "--url"),
    output: str = typer.Option("json", "--output", "-o",
        help="Output format: json (default) or table."),
    jq_filter: str | None = typer.Option(None, "--jq", help="jq filter expression"),
) -> None:
    """Zotero quick-search (title, creator, year, tags)."""
    emit_or_die(rpc_or_die(new_rpc(url), "search.quick",
                             {"query": query, "limit": limit}),
                 output=output, jq_filter=jq_filter)


@search_app.command(
    "fulltext",
    epilog='Examples:\n\n    zotron search fulltext "attention is all you need"',
)
def search_fulltext(
    query: str = typer.Argument(...),
    limit: int = typer.Option(50, "--limit"),
    url: str = typer.Option(DEFAULT_URL, "--url"),
    output: str = typer.Option("json", "--output", "-o",
        help="Output format: json (default) or table."),
    jq_filter: str | None = typer.Option(None, "--jq", help="jq filter expression"),
) -> None:
    """Full-text search across PDF contents."""
    emit_or_die(rpc_or_die(new_rpc(url), "search.fulltext",
                             {"query": query, "limit": limit}),
                 output=output, jq_filter=jq_filter)


@search_app.command(
    "by-identifier",
    epilog="Examples:\n\n    zotron search by-identifier --doi 10.1038/nature12373\n\n    zotron search by-identifier --isbn 9780262035613",
)
def search_by_identifier(
    doi: str | None = typer.Option(None, "--doi"),
    isbn: str | None = typer.Option(None, "--isbn"),
    issn: str | None = typer.Option(None, "--issn"),
    url: str = typer.Option(DEFAULT_URL, "--url"),
) -> None:
    """Find an item by DOI / ISBN / ISSN."""
    params = {k: v for k, v in
              {"doi": doi, "isbn": isbn, "issn": issn}.items()
              if v}
    if not params:
        die("INVALID_ARGS", "give at least one of --doi/--isbn/--issn", 2)
    typer.echo(json.dumps(rpc_or_die(new_rpc(url),
                                      "search.byIdentifier", params)))
