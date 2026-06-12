"""Tests for ledgercore.io."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ledgercore.io import (
    content_hash,
    ensure_dir,
    merge_text,
    normalize_newlines,
    read_text,
    summarize_text,
    write_text,
)


class TestNormalizeNewlines:
    def test_crlf_to_lf(self) -> None:
        assert normalize_newlines("a\r\nb") == "a\nb"

    def test_cr_to_lf(self) -> None:
        assert normalize_newlines("a\rb") == "a\nb"

    def test_mixed(self) -> None:
        assert normalize_newlines("a\r\nb\rc\n") == "a\nb\nc\n"

    def test_no_change(self) -> None:
        assert normalize_newlines("abc") == "abc"


class TestEnsureDir:
    def test_creates_directories(self, tmp_path: Path) -> None:
        target = tmp_path / "a" / "b" / "c"
        ensure_dir(target)
        assert target.is_dir()

    def test_existing_dir(self, tmp_path: Path) -> None:
        ensure_dir(tmp_path)
        assert tmp_path.is_dir()


class TestReadText:
    def test_reads_utf8(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        p.write_text("hello", encoding="utf-8")
        assert read_text(p) == "hello"

    def test_normalizes_by_default(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        p.write_bytes(b"a\r\nb")
        assert read_text(p) == "a\nb"

    def test_no_normalize(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        p.write_bytes(b"a\r\nb")
        assert read_text(p, normalize=False) == "a\r\nb"


class TestWriteText:
    def test_writes_file(self, tmp_path: Path) -> None:
        p = tmp_path / "sub" / "f.txt"
        write_text(p, "hello")
        assert p.read_text(encoding="utf-8") == "hello"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        p = tmp_path / "x" / "y" / "f.txt"
        write_text(p, "data")
        assert p.exists()

    def test_normalizes_by_default(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        write_text(p, "a\r\nb")
        assert p.read_bytes() == b"a\nb"


class TestContentHash:
    def test_sha256(self) -> None:
        text = "hello"
        expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert content_hash(text) == expected

    def test_stable(self) -> None:
        assert content_hash("abc") == content_hash("abc")


class TestSummarizeText:
    def test_short_text(self) -> None:
        assert summarize_text("hello world") == "hello world"

    def test_collapses_whitespace(self) -> None:
        assert summarize_text("  a   b  \n  c  ") == "a b c"

    def test_truncates_long_text(self) -> None:
        text = "a " * 50
        result = summarize_text(text, max_chars=20)
        assert len(result) <= 23  # 20 + "..."
        assert result.endswith("...")

    def test_empty_string(self) -> None:
        assert summarize_text("") == ""


class TestMergeText:
    def test_appends(self) -> None:
        result = merge_text("first", "second")
        assert result == "first\n\nsecond"

    def test_prepends(self) -> None:
        result = merge_text("first", "second", prepend=True)
        assert result == "second\n\nfirst"

    def test_empty_current(self) -> None:
        assert merge_text("", "second") == "second"

    def test_empty_incoming(self) -> None:
        assert merge_text("first", "") == "first"

    def test_both_empty(self) -> None:
        assert merge_text("", "") == ""
