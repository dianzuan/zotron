"""CLI: tags namespace."""
from __future__ import annotations

import json

import typer

from zotron._cli_base import DEFAULT_URL, new_rpc, rpc_or_die, dry_run, emit_or_die

tags_app = typer.Typer(
    help="Inspect / rename / delete tags across the library.",
    no_args_is_help=True,
)


@tags_app.command(
    "list",
    epilog="Examples:\n\n    zotron tags list --limit 100",
)
def tags_list(
    limit: int = typer.Option(200, "--limit"),
    url: str = typer.Option(DEFAULT_URL, "--url"),
    output: str = typer.Option("json", "--output", "-o",
        help="Output format: json (default) or table."),
    jq_filter: str | None = typer.Option(None, "--jq", help="jq filter expression"),
) -> None:
    """List all tags in the library (flat)."""
    emit_or_die(rpc_or_die(new_rpc(url), "tags.list", {"limit": limit}),
                 output=output, jq_filter=jq_filter)


@tags_app.command(
    "rename",
    epilog='Examples:\n\n    zotron tags rename "todo" "to-read"',
)
def tags_rename(
    old: str = typer.Argument(...),
    new: str = typer.Argument(...),
    url: str = typer.Option(DEFAULT_URL, "--url"),
    dry_run_flag: bool = typer.Option(False, "--dry-run",
        help="Print intended RPC call as JSON; do not execute."),
) -> None:
    """Rename a tag across all items."""
    if dry_run_flag:
        dry_run("tags.rename", {"oldName": old, "newName": new})
    typer.echo(json.dumps(rpc_or_die(new_rpc(url), "tags.rename",
                                      {"oldName": old, "newName": new})))


@tags_app.command(
    "delete",
    epilog='Examples:\n\n    zotron tags delete "outdated-tag"',
)
def tags_delete(
    tag: str = typer.Argument(...),
    url: str = typer.Option(DEFAULT_URL, "--url"),
    dry_run_flag: bool = typer.Option(False, "--dry-run",
        help="Print intended RPC call as JSON; do not execute."),
) -> None:
    """Delete a tag library-wide (removes from every item that had it)."""
    if dry_run_flag:
        dry_run("tags.delete", {"tag": tag})
    typer.echo(json.dumps(rpc_or_die(new_rpc(url), "tags.delete",
                                      {"tag": tag})))
