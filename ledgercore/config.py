"""Shared ledger workspace configuration conventions."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ledgercore.errors import LedgerConfigError
from ledgercore.paths import ConfigLocator, locate_config

LEDGER_CONFIG_FILENAMES: tuple[str, ...] = (".ledger.toml", "ledger.toml")


def ledger_config_filenames(
    *legacy_filenames: str,
    include_visible: bool = True,
) -> tuple[str, ...]:
    """Return canonical ledger config names followed by legacy fallbacks."""
    base = LEDGER_CONFIG_FILENAMES if include_visible else (".ledger.toml",)
    return (*base, *legacy_filenames)


def locate_ledger_config(
    start: Path,
    *,
    legacy_filenames: tuple[str, ...] = (),
    default: bool = False,
    default_filename: str = ".ledger.toml",
) -> ConfigLocator | None:
    """Locate a canonical ledger config or a caller-provided legacy fallback."""
    return locate_config(
        start,
        ledger_config_filenames(*legacy_filenames),
        default_filename=default_filename if default else None,
    )


def select_tool_config(
    document: Mapping[str, Any],
    tool_name: str,
    *,
    table_name: str = "tools",
) -> Mapping[str, Any]:
    """Select and validate a tool-specific config table."""
    tools = document.get(table_name)
    if not isinstance(tools, Mapping):
        raise LedgerConfigError(f"missing [{table_name}] table")
    tool_config = tools.get(tool_name)
    if not isinstance(tool_config, Mapping):
        raise LedgerConfigError(f"missing [{table_name}.{tool_name}] table")
    return tool_config


def select_project_config(
    document: Mapping[str, Any],
    *,
    table_name: str = "project",
) -> Mapping[str, Any]:
    """Select and validate the shared project table, defaulting to empty."""
    project = document.get(table_name, {})
    if not isinstance(project, Mapping):
        raise LedgerConfigError(f"[{table_name}] must be a table")
    return project
