"""Tests for shared ledger configuration conventions."""

from __future__ import annotations

from pathlib import Path

import pytest

from ledgercore.config import (
    LEDGER_CONFIG_FILENAMES,
    LedgerConfigError,
    ledger_config_filenames,
    locate_ledger_config,
    select_project_config,
    select_tool_config,
)


def test_default_filenames_prefer_hidden() -> None:
    assert LEDGER_CONFIG_FILENAMES == (".ledger.toml", "ledger.toml")


def test_ledger_config_filenames_appends_legacy() -> None:
    assert ledger_config_filenames(".legacy.toml", "legacy.toml") == (
        ".ledger.toml",
        "ledger.toml",
        ".legacy.toml",
        "legacy.toml",
    )


def test_ledger_config_filenames_can_exclude_visible() -> None:
    assert ledger_config_filenames(
        ".legacy.toml",
        include_visible=False,
    ) == (".ledger.toml", ".legacy.toml")


def test_locate_ledger_config_prefers_dot_ledger_toml(tmp_path: Path) -> None:
    visible = tmp_path / "ledger.toml"
    hidden = tmp_path / ".ledger.toml"
    visible.write_text("visible", encoding="utf-8")
    hidden.write_text("hidden", encoding="utf-8")

    result = locate_ledger_config(tmp_path)

    assert result is not None
    assert result.config_path == hidden
    assert result.workspace_root == tmp_path


def test_locate_ledger_config_prefers_canonical_over_legacy(tmp_path: Path) -> None:
    canonical = tmp_path / "ledger.toml"
    legacy = tmp_path / ".legacy.toml"
    canonical.write_text("canonical", encoding="utf-8")
    legacy.write_text("legacy", encoding="utf-8")

    result = locate_ledger_config(
        tmp_path,
        legacy_filenames=(".legacy.toml", "legacy.toml"),
    )

    assert result is not None
    assert result.config_path == canonical


def test_locate_ledger_config_falls_back_to_legacy(tmp_path: Path) -> None:
    legacy = tmp_path / ".legacy.toml"
    legacy.write_text("legacy", encoding="utf-8")

    result = locate_ledger_config(
        tmp_path,
        legacy_filenames=(".legacy.toml", "legacy.toml"),
    )

    assert result is not None
    assert result.config_path == legacy


def test_locate_ledger_config_default_uses_dot_ledger(tmp_path: Path) -> None:
    result = locate_ledger_config(tmp_path, default=True)

    assert result is not None
    assert result.source == "default"
    assert result.config_path == (tmp_path / ".ledger.toml").resolve()


def test_locate_ledger_config_accepts_custom_default_filename(
    tmp_path: Path,
) -> None:
    result = locate_ledger_config(
        tmp_path,
        default=True,
        default_filename="custom.toml",
    )

    assert result is not None
    assert result.config_path == (tmp_path / "custom.toml").resolve()


def test_select_tool_config() -> None:
    doc = {"tools": {"example": {"config_version": 2}}}

    assert select_tool_config(doc, "example") == {"config_version": 2}


def test_select_tool_config_accepts_custom_table_name() -> None:
    doc = {"extensions": {"example": {"enabled": True}}}

    assert select_tool_config(
        doc,
        "example",
        table_name="extensions",
    ) == {"enabled": True}


@pytest.mark.parametrize(
    ("document", "message"),
    [
        ({}, "missing [tools] table"),
        ({"tools": []}, "missing [tools] table"),
        ({"tools": {}}, "missing [tools.example] table"),
        ({"tools": {"example": "invalid"}}, "missing [tools.example] table"),
    ],
)
def test_select_tool_config_rejects_missing_or_invalid_tables(
    document: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(LedgerConfigError) as exc_info:
        select_tool_config(document, "example")
    assert str(exc_info.value) == message


def test_select_project_config_defaults_empty() -> None:
    assert select_project_config({}) == {}


def test_select_project_config() -> None:
    project = {"uuid": "123", "name": "example"}

    assert select_project_config({"project": project}) == project


def test_select_project_config_accepts_custom_table_name() -> None:
    shared = {"name": "example"}

    assert select_project_config({"shared": shared}, table_name="shared") == shared


def test_select_project_config_rejects_non_mapping() -> None:
    with pytest.raises(LedgerConfigError, match=r"\[project\] must be a table"):
        select_project_config({"project": []})
