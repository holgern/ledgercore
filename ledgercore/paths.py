"""Path validation and discovery utilities for ledgercore."""

from __future__ import annotations

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
) -> str:
    """Validate that a path is a safe relative POSIX path."""
    if not value:
        raise PathValidationError(f"{field_name} must not be empty")
    if "\\" in value:
        raise PathValidationError(
            f"{field_name} must not contain backslashes: {value}"
        )
    if value.startswith("/"):
        raise PathValidationError(
            f"{field_name} must be relative, not absolute: {value}"
        )

    segments = value.split("/")
    for seg in segments:
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
