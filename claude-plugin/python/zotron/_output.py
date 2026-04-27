"""Output formatting helpers for the typer CLI.

Centralizes the JSON-vs-table decision so individual commands stay terse.
Not part of the SDK public surface (leading underscore).
"""
from __future__ import annotations

import io
import json
from typing import Any


def emit(
    data: Any,
    *,
    output: str = "json",
    jq_filter: str | None = None,
) -> None:
    """Print `data` to stdout in the requested format.

    output="json"  : compact JSON (ensure_ascii=False, indent=2)
    output="table" : Rich-rendered table when shape is list-of-dicts or
                     a flat dict; falls back to JSON for nested data.

    jq_filter : optional jq expression. Runs BEFORE the json/table
                dispatch so `--jq` and `--output table` compose. Multi-
                result programs return a list; single result is unwrapped.
    """
    if jq_filter is not None:
        try:
            import jq as jq_lib  # type: ignore[import-not-found]
        except ImportError as e:
            raise RuntimeError(
                "jq library required for --jq; install with `pip install jq`"
            ) from e
        try:
            program = jq_lib.compile(jq_filter)
        except ValueError as e:
            raise ValueError(f"invalid jq expression: {e}") from e
        try:
            results = program.input_value(data).all()
        except ValueError as e:
            # jq raises ValueError at runtime too (e.g. wrong-type indexing).
            # Unify with compile-time errors so the CLI's INVALID_JQ envelope
            # catches both paths.
            raise ValueError(f"invalid jq expression: {e}") from e
        # Unwrap single result for cleanliness; multi-result stays as a list.
        data = results[0] if len(results) == 1 else results

    if output == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if output == "table":
        rendered = _render_table(data)
        if rendered is None:
            # Fallback — nested / scalar data has no clean table form.
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            # Print the pre-rendered string. Going through a Console
            # buffer (rather than Console(file=sys.stdout)) keeps stdout
            # capture compatible with both CliRunner and capsys.
            print(rendered, end="")
        return
    raise ValueError(f"unknown output: {output!r}")


def _render_table(data: Any) -> str | None:
    """Return the rendered table string, or None if `data` has no clean
    tabular form (caller should fall back to JSON)."""
    from rich.console import Console
    from rich.table import Table

    if isinstance(data, list) and data and all(isinstance(r, dict) for r in data):
        # Union of keys, preserving first-row order, appending new ones.
        cols: list[str] = []
        seen: set[str] = set()
        for row in data:
            for k in row.keys():
                if k not in seen:
                    seen.add(k)
                    cols.append(k)
        # Bail if any cell is itself nested — not a flat table.
        for row in data:
            for k in cols:
                if isinstance(row.get(k), (dict, list)):
                    return None
        table = Table(show_header=True, header_style="bold")
        for c in cols:
            table.add_column(c)
        for row in data:
            table.add_row(*[("" if row.get(c) is None else str(row.get(c)))
                            for c in cols])
    elif isinstance(data, dict) and not any(
        isinstance(v, (dict, list)) for v in data.values()
    ):
        table = Table(show_header=True, header_style="bold")
        table.add_column("key")
        table.add_column("value")
        for k, v in data.items():
            table.add_row(str(k), "" if v is None else str(v))
    else:
        return None

    # Render to an in-memory string buffer so we can hand stdout-printing
    # back to plain print() for capture compatibility.
    buf = io.StringIO()
    Console(file=buf, soft_wrap=True, force_terminal=False).print(table)
    return buf.getvalue()
