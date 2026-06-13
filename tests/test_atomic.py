"""Tests for ledgercore.atomic."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

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

    def test_cleans_up_tmp_on_failure(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        with patch("os.replace", side_effect=OSError("replace failed")):
            with pytest.raises(AtomicWriteError, match="Atomic write failed"):
                atomic_write_text(p, "fail")
        tmp_files = list(tmp_path.glob(".ledgercore-tmp-*"))
        assert tmp_files == []

    def test_preserves_original_cause(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        with patch("os.replace", side_effect=OSError("replace failed")):
            with pytest.raises(AtomicWriteError) as exc_info:
                atomic_write_text(p, "fail")
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, OSError)


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

    def test_does_not_overwrite_existing_content(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        p.write_text("original", encoding="utf-8")
        with pytest.raises(AtomicWriteError):
            atomic_create_text(p, "new")
        assert p.read_text(encoding="utf-8") == "original"

    def test_race_safe_concurrent_create(self, tmp_path: Path) -> None:
        """Simulate a race: another process creates the file after our check.

        With O_CREAT|O_EXCL, the OS guarantees atomicity, so this test
        verifies the error is raised when the file appears concurrently.
        """
        p = tmp_path / "f.txt"
        # Pre-create the file to simulate a concurrent creator
        p.write_text("concurrent", encoding="utf-8")
        with pytest.raises(AtomicWriteError, match="already exists"):
            atomic_create_text(p, "my content")

    def test_fsync_skipped_by_env_var(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        os.environ["_LEDGERCORE_TEST_FAST"] = "1"
        try:
            atomic_create_text(p, "fast", fast_io_env_var="_LEDGERCORE_TEST_FAST")
        finally:
            del os.environ["_LEDGERCORE_TEST_FAST"]
        assert p.read_text(encoding="utf-8") == "fast"

    def test_preserves_original_cause(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        p.write_text("old", encoding="utf-8")
        with pytest.raises(AtomicWriteError) as exc_info:
            atomic_create_text(p, "new")
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, FileExistsError)

    def test_handles_partial_os_write(self, tmp_path: Path) -> None:
        """A partial os.write must still produce a complete file."""
        p = tmp_path / "f.txt"
        content = "abcdefghij"

        real_write = os.write
        call = {"n": 0}

        def short_write(fd: int, data: bytes) -> int:
            # First call writes only the first byte; subsequent calls write normally.
            call["n"] += 1
            if call["n"] == 1:
                return real_write(fd, data[:1])
            return real_write(fd, data)

        with patch("ledgercore.atomic.os.write", side_effect=short_write) as _:
            atomic_create_text(p, content, fsync=False)
        assert p.read_text(encoding="utf-8") == content
