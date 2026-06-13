"""Tests for ledgercore.paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from ledgercore.errors import PathValidationError
from ledgercore.paths import (
    ensure_inside_base,
    find_config_upwards,
    is_relative_to,
    locate_config,
    relative_to_base,
    resolve_config_relative_path,
    resolve_relative_child,
    resolve_under_base,
    validate_relative_posix_path,
)


class TestBaseRelativeHelpers:
    def test_inside_and_same_are_accepted(self, tmp_path: Path) -> None:
        assert ensure_inside_base(tmp_path, tmp_path) == tmp_path.resolve()
        assert ensure_inside_base(
            tmp_path, tmp_path / "child"
        ) == (tmp_path / "child").resolve()

    def test_outside_is_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(PathValidationError, match="escapes"):
            ensure_inside_base(tmp_path / "base", tmp_path / "sibling")

    def test_relative_uses_posix_text(self, tmp_path: Path) -> None:
        assert relative_to_base(tmp_path, tmp_path / "a" / "b") == "a/b"

    def test_resolve_under_base_checks_existence(self, tmp_path: Path) -> None:
        with pytest.raises(PathValidationError, match="does not exist"):
            resolve_under_base(tmp_path, "missing", allow_missing=False)

    def test_resolve_under_base_rejects_escape(self, tmp_path: Path) -> None:
        with pytest.raises(PathValidationError):
            resolve_under_base(tmp_path, "../escape")


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

    def test_empty_segment(self) -> None:
        with pytest.raises(PathValidationError, match="empty segment"):
            validate_relative_posix_path("a//b")

    def test_trailing_slash_rejected(self) -> None:
        with pytest.raises(PathValidationError, match="trailing slash"):
            validate_relative_posix_path("a/")

    def test_trailing_slash_allowed(self) -> None:
        assert validate_relative_posix_path("a/", allow_trailing_slash=True) == "a/"

    def test_dot_slash(self) -> None:
        with pytest.raises(PathValidationError, match="'.'"):
            validate_relative_posix_path("./a")

    def test_trailing_dot(self) -> None:
        with pytest.raises(PathValidationError, match="'.'"):
            validate_relative_posix_path("a/.")


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

    def test_search_from_file(self, tmp_path: Path) -> None:
        config = tmp_path / "config.toml"
        config.write_text("test")
        child = tmp_path / "sub" / "file.py"
        child.parent.mkdir(parents=True)
        child.write_text("")
        assert find_config_upwards(child, ("config.toml",)) == config


class TestLocateConfig:
    def test_finds_config(self, tmp_path: Path) -> None:
        config = tmp_path / "myapp.toml"
        config.write_text("test")
        result = locate_config(tmp_path, ("myapp.toml",))
        assert result is not None
        assert result.config_path == config
        assert result.workspace_root == tmp_path
        assert result.source == "found"

    def test_visible_preferred_over_hidden(self, tmp_path: Path) -> None:
        visible = tmp_path / "myapp.toml"
        hidden = tmp_path / ".myapp.toml"
        visible.write_text("visible")
        hidden.write_text("hidden")
        result = locate_config(tmp_path, ("myapp.toml", ".myapp.toml"))
        assert result is not None
        assert result.config_path == visible

    def test_hidden_found_when_requested(self, tmp_path: Path) -> None:
        hidden = tmp_path / ".myapp.toml"
        hidden.write_text("hidden")
        result = locate_config(tmp_path, (".myapp.toml",))
        assert result is not None
        assert result.config_path == hidden

    def test_no_config_no_default(self, tmp_path: Path) -> None:
        result = locate_config(tmp_path, ("missing.toml",))
        assert result is None

    def test_default_filename(self, tmp_path: Path) -> None:
        result = locate_config(
            tmp_path, ("missing.toml",), default_filename="myapp.toml"
        )
        assert result is not None
        assert result.source == "default"
        assert result.config_path == (tmp_path / "myapp.toml").resolve()
        assert result.workspace_root == tmp_path.resolve()

    def test_search_from_nested_directory(self, tmp_path: Path) -> None:
        config = tmp_path / "config.toml"
        config.write_text("test")
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)
        result = locate_config(nested, ("config.toml",))
        assert result is not None
        assert result.config_path == config

    def test_search_from_file(self, tmp_path: Path) -> None:
        config = tmp_path / "config.toml"
        config.write_text("test")
        start_file = tmp_path / "src" / "main.py"
        start_file.parent.mkdir(parents=True)
        start_file.write_text("")
        result = locate_config(start_file, ("config.toml",))
        assert result is not None
        assert result.config_path == config


class TestResolveConfigRelativePath:
    def test_resolves_relative(self, tmp_path: Path) -> None:
        config = tmp_path / "myapp.toml"
        config.write_text("")
        result = resolve_config_relative_path(
            config, "data/store", field_name="storage_dir"
        )
        assert result == (tmp_path / "data" / "store").resolve()

    def test_rejects_absolute(self, tmp_path: Path) -> None:
        config = tmp_path / "myapp.toml"
        config.write_text("")
        with pytest.raises(PathValidationError, match="absolute"):
            resolve_config_relative_path(
                config, "/absolute/path", field_name="storage_dir"
            )

    def test_rejects_escape(self, tmp_path: Path) -> None:
        config = tmp_path / "myapp.toml"
        config.write_text("")
        with pytest.raises(PathValidationError):
            resolve_config_relative_path(
                config, "../../escape", field_name="storage_dir"
            )
