"""Path validation and discovery utilities for ledgercore."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ledgercore.errors import PathValidationError


def is_relative_to(path: Path, parent: Path) -> bool:
    """Check whether path is relative to parent."""
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def validate_relative_posix_path(
    value: str,
    *,
    field_name: str = "path",
    allow_trailing_slash: bool = False,
) -> str:
    """Validate that a path is a safe relative POSIX path."""
    if not value:
        raise PathValidationError(f"{field_name} must not be empty")
    if "\\" in value:
        raise PathValidationError(f"{field_name} must not contain backslashes: {value}")
    if value.startswith("/"):
        raise PathValidationError(
            f"{field_name} must be relative, not absolute: {value}"
        )
    if not allow_trailing_slash and value.endswith("/"):
        raise PathValidationError(
            f"{field_name} must not end with a trailing slash: {value}"
        )

    segments = value.split("/")
    # When trailing slash is allowed, the split may produce a trailing empty
    # segment; skip it.
    if allow_trailing_slash and segments and not segments[-1]:
        segments = segments[:-1]
    for seg in segments:
        if not seg:
            raise PathValidationError(
                f"{field_name} must not contain empty segments: {value}"
            )
        if seg in (".", ".."):
            raise PathValidationError(
                f"{field_name} must not contain '.' or '..' segments: {value}"
            )

    return value


def resolve_relative_child(
    base_dir: Path,
    relative_path: str,
    *,
    field_name: str = "path",
) -> Path:
    """Validate and resolve a relative path under a base directory."""
    validate_relative_posix_path(relative_path, field_name=field_name)
    resolved = (base_dir / relative_path).resolve()
    base_resolved = base_dir.resolve()
    try:
        resolved.relative_to(base_resolved)
    except ValueError:
        raise PathValidationError(
            f"{field_name} escapes base directory: {relative_path}"
        ) from None
    return resolved


def ensure_inside_base(
    base_dir: Path, path: Path, *, field_name: str = "path"
) -> Path:
    """Resolve path and require it to be inside or equal to base_dir."""
    base_resolved = base_dir.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(base_resolved)
    except ValueError:
        raise PathValidationError(
            f"{field_name} escapes base directory: {path}"
        ) from None
    return resolved


def relative_to_base(
    base_dir: Path, path: Path, *, field_name: str = "path"
) -> str:
    """Return a safe base-relative path using POSIX separators."""
    resolved = ensure_inside_base(base_dir, path, field_name=field_name)
    return resolved.relative_to(base_dir.resolve()).as_posix()


def resolve_under_base(
    base_dir: Path,
    relative_path: str,
    *,
    field_name: str = "path",
    allow_missing: bool = True,
) -> Path:
    """Resolve a validated relative path below base_dir."""
    resolved = resolve_relative_child(
        base_dir, relative_path, field_name=field_name
    )
    if not allow_missing and not resolved.exists():
        raise PathValidationError(f"{field_name} does not exist: {relative_path}")
    return resolved


def find_config_upwards(
    start: Path,
    filenames: tuple[str, ...],
) -> Path | None:
    """Walk from start upward, returning the first matching file, or None."""
    current = start.resolve()
    while True:
        for name in filenames:
            candidate = current / name
            if candidate.is_file():
                return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent


@dataclass(frozen=True)
class ConfigLocator:
    """Result of a config file search."""

    workspace_root: Path
    config_path: Path
    source: str


def locate_config(
    start: Path,
    filenames: tuple[str, ...],
    *,
    default_filename: str | None = None,
) -> ConfigLocator | None:
    """Find a config file and return both its path and the workspace root.

    Args:
        start: Directory or file to start searching from.
        filenames: Ordered candidate filenames to search for.
        default_filename: If provided and no config is found, create a
            locator pointing at start/default_filename without checking
            existence.

    Returns:
        ConfigLocator with workspace_root and config_path, or None.
    """
    search_start = start.resolve()
    if search_start.is_file():
        search_start = search_start.parent

    config_path = find_config_upwards(search_start, filenames)
    if config_path is not None:
        return ConfigLocator(
            workspace_root=config_path.parent,
            config_path=config_path,
            source="found",
        )

    if default_filename is not None:
        default_path = (search_start / default_filename).resolve()
        return ConfigLocator(
            workspace_root=search_start,
            config_path=default_path,
            source="default",
        )

    return None


def resolve_config_relative_path(
    config_path: Path,
    value: str,
    *,
    field_name: str,
) -> Path:
    """Resolve a relative path relative to the config file's directory.

    Absolute values are rejected by default.
    """
    if value.startswith("/"):
        raise PathValidationError(
            f"{field_name} must be relative to config, not absolute: {value}"
        )
    validate_relative_posix_path(value, field_name=field_name)
    config_dir = config_path.parent.resolve()
    resolved = (config_dir / value).resolve()
    try:
        resolved.relative_to(config_dir)
    except ValueError:
        raise PathValidationError(
            f"{field_name} escapes config directory: {value}"
        ) from None
    return resolved
