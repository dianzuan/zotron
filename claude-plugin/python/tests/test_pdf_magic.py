"""Tests for zotron.push.check_pdf_magic."""
from pathlib import Path
from zotron.push import check_pdf_magic


def test_valid_pdf(tmp_path: Path):
    p = tmp_path / "good.pdf"
    p.write_bytes(b"%PDF-1.7\n%...\nrest of a fake pdf")
    assert check_pdf_magic(p) is True


def test_html_masquerading_as_pdf(tmp_path: Path):
    p = tmp_path / "evil.pdf"
    p.write_bytes(b"<!DOCTYPE html><html>...")
    assert check_pdf_magic(p) is False


def test_empty_file(tmp_path: Path):
    p = tmp_path / "empty.pdf"
    p.write_bytes(b"")
    assert check_pdf_magic(p) is False


def test_too_short(tmp_path: Path):
    p = tmp_path / "tiny.pdf"
    p.write_bytes(b"%PD")   # only 3 bytes
    assert check_pdf_magic(p) is False


def test_nonexistent_file(tmp_path: Path):
    p = tmp_path / "missing.pdf"
    # File does not exist
    assert check_pdf_magic(p) is False
