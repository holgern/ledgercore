"""Tests for ledgercore.atomic."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ledgercore.atomic import atomic_create_text, atomic_write_text
from ledgercore.errors import AtomicWriteError


class TestAtomicWriteText:
    def test_writes_file(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        atomic_write_text(p, "hello")
        assert p.read_text(encoding="utf-8") == "hello"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        p = tmp_path / "a" / "b" / "f.txt"
        atomic_write_text(p, "data")
        assert p.read_text(encoding="utf-8") == "data"

    def test_replaces_existing(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        p.write_text("old", encoding="utf-8")
        atomic_write_text(p, "new")
        assert p.read_text(encoding="utf-8") == "new"

    def test_normalize(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        atomic_write_text(p, "a\r\nb", normalize=True)
        assert p.read_text(encoding="utf-8") == "a\nb"

    def test_no_normalize(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        atomic_write_text(p, "a\r\nb", normalize=False)
        assert p.read_bytes() == b"a\r\nb"

    def test_fsync_skipped_by_env_var(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        os.environ["_LEDGERCORE_TEST_FAST"] = "1"
        try:
            atomic_write_text(p, "fast", fast_io_env_var="_LEDGERCORE_TEST_FAST")
        finally:
            del os.environ["_LEDGERCORE_TEST_FAST"]
        assert p.read_text(encoding="utf-8") == "fast"

    def test_no_tmp_files_on_success(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        atomic_write_text(p, "clean")
        tmp_files = list(tmp_path.glob(".ledgercore-tmp-*"))
        assert tmp_files == []


class TestAtomicCreateText:
    def test_creates_new_file(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        atomic_create_text(p, "new")
        assert p.read_text(encoding="utf-8") == "new"

    def test_fails_if_exists(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        p.write_text("old", encoding="utf-8")
        with pytest.raises(AtomicWriteError, match="already exists"):
            atomic_create_text(p, "new")

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        p = tmp_path / "sub" / "f.txt"
        atomic_create_text(p, "data")
        assert p.read_text(encoding="utf-8") == "data"
