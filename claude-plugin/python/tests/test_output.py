"""Tests for zotron._output.emit and _render_table."""
import json

import pytest

from zotron._output import emit


def test_emit_json_default_round_trips(capsys):
    emit({"id": 1, "name": "x"})
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"id": 1, "name": "x"}


def test_emit_json_handles_unicode(capsys):
    emit({"name": "案例库"})
    captured = capsys.readouterr()
    # ensure_ascii=False — 中文 should render literally
    assert "案例库" in captured.out


def test_emit_table_list_of_dicts(capsys):
    rows = [
        {"id": 1, "name": "Research", "parentID": None},
        {"id": 2, "name": "Teaching", "parentID": 1},
    ]
    emit(rows, output="table")
    out = capsys.readouterr().out
    # Headers + values present
    assert "id" in out and "name" in out and "parentID" in out
    assert "Research" in out and "Teaching" in out


def test_emit_table_dict_renders_key_value(capsys):
    emit({"id": 12345, "title": "Attention is all you need"}, output="table")
    out = capsys.readouterr().out
    assert "id" in out and "12345" in out
    assert "title" in out and "Attention" in out


def test_emit_table_falls_back_to_json_for_nested(capsys):
    """Deeply nested data has no clean table form — fall back to JSON,
    not crash."""
    emit({"tree": {"id": 1, "children": [{"id": 2}]}}, output="table")
    out = capsys.readouterr().out
    # Should still be valid JSON in this fallback
    assert "children" in out


def test_emit_rejects_unknown_output():
    with pytest.raises(ValueError, match="unknown output"):
        emit({"x": 1}, output="xml")


def test_emit_jq_filters_list(capsys):
    rows = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
    emit(rows, jq_filter=".[].name")
    out = capsys.readouterr().out
    assert '"a"' in out and '"b"' in out
    # Should NOT contain the id key
    assert '"id"' not in out


def test_emit_jq_filters_dict(capsys):
    emit({"itemKey": "ABC", "title": "Foo"}, jq_filter=".itemKey")
    out = capsys.readouterr().out
    assert '"ABC"' in out
    assert '"title"' not in out


def test_emit_jq_invalid_expression_raises():
    import pytest
    with pytest.raises(ValueError, match="invalid jq"):
        emit([{"id": 1}], jq_filter="[[[broken")


def test_emit_jq_runtime_error_raises_value_error():
    """A jq expression that compiles but fails at runtime (e.g. wrong
    type indexing) must raise ValueError, not bubble jq's exception."""
    with pytest.raises(ValueError, match="invalid jq"):
        # `[.[] | {id}]` on a dict iterates values, then tries to index
        # each value. For values that aren't dicts/null, jq raises
        # "Cannot index <type> with string \"id\"" at runtime.
        emit({"items": [{"id": 1}], "total": 1},
             jq_filter='[.[] | {id}]')
