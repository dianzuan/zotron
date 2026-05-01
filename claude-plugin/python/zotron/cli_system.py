"""CLI: system namespace."""
from __future__ import annotations

import json

import typer

from zotron._cli_base import DEFAULT_URL, new_rpc, rpc_or_die, emit_or_die

system_app = typer.Typer(
    help="Plugin version, trigger sync, list libraries.",
    no_args_is_help=True,
)


@system_app.command(
    "version",
    epilog="Examples:\n\n    zotron system version",
)
def system_version(
    url: str = typer.Option(DEFAULT_URL, "--url"),
    jq_filter: str | None = typer.Option(None, "--jq", help="jq filter expression"),
) -> None:
    """Show XPI version + the methods it exposes."""
    emit_or_die(rpc_or_die(new_rpc(url), "system.version"), jq_filter=jq_filter)


@system_app.command(
    "sync",
    epilog="Examples:\n\n    zotron system sync",
)
def system_sync(
    url: str = typer.Option(DEFAULT_URL, "--url"),
) -> None:
    """Trigger a Zotero sync (cloud <-> local)."""
    typer.echo(json.dumps(rpc_or_die(new_rpc(url), "system.sync")))


@system_app.command(
    "libraries",
    epilog="Examples:\n\n    zotron system libraries",
)
def system_libraries(
    url: str = typer.Option(DEFAULT_URL, "--url"),
    output: str = typer.Option("json", "--output", "-o",
        help="Output format: json (default) or table."),
    jq_filter: str | None = typer.Option(None, "--jq", help="jq filter expression"),
) -> None:
    """List all libraries (user + groups)."""
    emit_or_die(rpc_or_die(new_rpc(url), "system.libraries"),
                 output=output, jq_filter=jq_filter)
