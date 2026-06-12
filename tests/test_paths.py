"""Tests for ledgercore.paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from ledgercore.errors import PathValidationError
from ledgercore.paths import (
    find_config_upwards,
    is_relative_to,
    resolve_relative_child,
    validate_relative_posix_path,
)


class TestIsRelativeTo:
    def test_child(self, tmp_path: Path) -> None:
        assert is_relative_to(tmp_path / "a" / "b", tmp_path)

    def test_same(self, tmp_path: Path) -> None:
        assert is_relative_to(tmp_path, tmp_path)

    def test_unrelated(self, tmp_path: Path) -> None:
        assert not is_relative_to(Path("/other"), tmp_path)


class TestValidateRelativePosixPath:
    def test_valid(self) -> None:
        assert validate_relative_posix_path("a/b/c.txt") == "a/b/c.txt"

    def test_empty(self) -> None:
        with pytest.raises(PathValidationError, match="empty"):
            validate_relative_posix_path("")

    def test_absolute(self) -> None:
        with pytest.raises(PathValidationError, match="absolute"):
            validate_relative_posix_path("/etc/passwd")

    def test_backslash(self) -> None:
        with pytest.raises(PathValidationError, match="backslash"):
            validate_relative_posix_path("a\\b")

    def test_dot_segment(self) -> None:
        with pytest.raises(PathValidationError, match="'.'"):
            validate_relative_posix_path("a/./b")

    def test_dotdot_segment(self) -> None:
        with pytest.raises(PathValidationError, match="'.'"):
            validate_relative_posix_path("../a")

    def test_custom_field_name(self) -> None:
        with pytest.raises(PathValidationError, match="myfield"):
            validate_relative_posix_path("", field_name="myfield")


class TestResolveRelativeChild:
    def test_resolves(self, tmp_path: Path) -> None:
        result = resolve_relative_child(tmp_path, "a/b.txt")
        assert result == (tmp_path / "a" / "b.txt").resolve()

    def test_rejects_dotdot(self, tmp_path: Path) -> None:
        with pytest.raises(PathValidationError, match="\\.\\."):
            resolve_relative_child(tmp_path, "../../etc/passwd")

    def test_rejects_absolute(self, tmp_path: Path) -> None:
        with pytest.raises(PathValidationError, match="absolute"):
            resolve_relative_child(tmp_path, "/etc/passwd")


class TestFindConfigUpwards:
    def test_finds_in_start(self, tmp_path: Path) -> None:
        config = tmp_path / "taskledger.toml"
        config.write_text("test")
        assert find_config_upwards(tmp_path, ("taskledger.toml",)) == config

    def test_finds_in_parent(self, tmp_path: Path) -> None:
        config = tmp_path / "config.toml"
        config.write_text("test")
        child = tmp_path / "sub"
        child.mkdir()
        assert find_config_upwards(child, ("config.toml",)) == config

    def test_not_found(self, tmp_path: Path) -> None:
        assert find_config_upwards(tmp_path, ("nonexistent.toml",)) is None

    def test_multiple_filenames(self, tmp_path: Path) -> None:
        config = tmp_path / "b.toml"
        config.write_text("test")
        assert find_config_upwards(tmp_path, ("a.toml", "b.toml")) == config
