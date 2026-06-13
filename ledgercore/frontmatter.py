"""YAML front matter read/write and file iteration for ledgercore."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Literal

import yaml

from ledgercore.errors import FrontMatterError

MissingFrontMatterMode = Literal["error", "empty"]
BodyMode = Literal[
    "preserve", "ensure-single-final-newline", "strip-leading-blank"
]
ScalarStyle = Literal["minimal", "pyyaml"]

_FRONT_MATTER_DELIM = "---"
_TEMPLATE_VALUE = re.compile(
    r"^(\s*[^#\n][^:\n]*:\s*)(\{\{[^{}\n]+\}\})(\s*(?:#.*)?)$",
    re.MULTILINE,
)


class _StringTimestampSafeLoader(yaml.SafeLoader):
    """Safe YAML loader that does not construct timestamps."""


_StringTimestampSafeLoader.yaml_implicit_resolvers = deepcopy(
    yaml.SafeLoader.yaml_implicit_resolvers
)
for first_char, resolvers in list(
    _StringTimestampSafeLoader.yaml_implicit_resolvers.items()
):
    _StringTimestampSafeLoader.yaml_implicit_resolvers[first_char] = [
        resolver
        for resolver in resolvers
        if resolver[0] != "tag:yaml.org,2002:timestamp"
    ]


def _quote_template_values(yaml_block: str) -> str:
    def replace(match: re.Match[str]) -> str:
        value = match.group(2).replace("'", "''")
        return f"{match.group(1)}'{value}'{match.group(3)}"

    return _TEMPLATE_VALUE.sub(replace, yaml_block)


def _split_document(text: str) -> tuple[str, str]:
    rest = text[len(_FRONT_MATTER_DELIM) + 1 :]
    if rest.startswith(_FRONT_MATTER_DELIM + "\n"):
        return "", rest[len(_FRONT_MATTER_DELIM) + 1 :]
    if rest == _FRONT_MATTER_DELIM:
        return "", ""

    close = rest.find("\n" + _FRONT_MATTER_DELIM + "\n")
    if close >= 0:
        return (
            rest[:close],
            rest[close + len("\n" + _FRONT_MATTER_DELIM + "\n") :],
        )
    if rest.endswith("\n" + _FRONT_MATTER_DELIM):
        return rest[: -len("\n" + _FRONT_MATTER_DELIM)], ""
    raise FrontMatterError("No closing '---' delimiter found")


def split_front_matter_text(
    text: str,
    *,
    missing: MissingFrontMatterMode = "error",
    preserve_yaml_timestamps_as_strings: bool = False,
    quote_template_placeholders: bool = False,
) -> tuple[dict[str, object], str]:
    """Split YAML front matter from an in-memory document."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith(_FRONT_MATTER_DELIM + "\n"):
        if missing == "empty":
            return {}, text
        raise FrontMatterError(
            "Document must start with '---' followed by a newline"
        )

    yaml_block, body = _split_document(normalized)
    if not yaml_block.strip():
        return {}, body
    if quote_template_placeholders:
        yaml_block = _quote_template_values(yaml_block)

    loader = (
        _StringTimestampSafeLoader
        if preserve_yaml_timestamps_as_strings
        else yaml.SafeLoader
    )
    try:
        loaded = yaml.load(yaml_block, Loader=loader)
    except yaml.YAMLError as exc:
        raise FrontMatterError(f"Invalid YAML: {exc}") from exc
    if loaded is None:
        return {}, body
    if not isinstance(loaded, dict):
        raise FrontMatterError(
            "YAML front matter must be a mapping, "
            f"got {type(loaded).__name__}"
        )
    return dict(loaded), body


def _ordered_metadata(
    metadata: Mapping[str, object], key_order: Sequence[str]
) -> dict[str, object]:
    ordered: dict[str, object] = {}
    for key in key_order:
        if key in metadata:
            ordered[key] = metadata[key]
    for key, value in metadata.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def render_front_matter_text(
    metadata: Mapping[str, object],
    body: str = "",
    *,
    key_order: Sequence[str] = (),
    body_mode: BodyMode = "preserve",
    scalar_style: ScalarStyle = "minimal",
) -> str:
    """Render metadata and body as a YAML front matter document."""
    if body_mode == "ensure-single-final-newline":
        body = body.rstrip("\n") + "\n" if body else body
    elif body_mode == "strip-leading-blank":
        body = body.lstrip("\n")
    elif body_mode != "preserve":
        raise ValueError(f"Unsupported body mode: {body_mode}")
    if scalar_style not in ("minimal", "pyyaml"):
        raise ValueError(f"Unsupported scalar style: {scalar_style}")

    yaml_block = yaml.safe_dump(
        _ordered_metadata(metadata, key_order),
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    if not yaml_block.endswith("\n"):
        yaml_block += "\n"
    return f"{_FRONT_MATTER_DELIM}\n{yaml_block}{_FRONT_MATTER_DELIM}\n{body}"


def update_front_matter_text(
    text: str,
    updates: Mapping[str, object],
    *,
    missing: MissingFrontMatterMode = "empty",
    key_order: Sequence[str] = (),
    preserve_yaml_timestamps_as_strings: bool = False,
    quote_template_placeholders: bool = False,
) -> str:
    """Update metadata in an in-memory front matter document."""
    metadata, body = split_front_matter_text(
        text,
        missing=missing,
        preserve_yaml_timestamps_as_strings=preserve_yaml_timestamps_as_strings,
        quote_template_placeholders=quote_template_placeholders,
    )
    metadata.update(updates)
    return render_front_matter_text(metadata, body, key_order=key_order)


def read_front_matter_document(path: Path) -> tuple[dict[str, object], str]:
    """Read a YAML front matter document, returning (metadata, body)."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FrontMatterError(f"Cannot read {path}: {exc}") from exc

    try:
        return split_front_matter_text(raw)
    except FrontMatterError as exc:
        raise FrontMatterError(f"{exc}: {path}") from exc


def write_front_matter_document(
    path: Path,
    metadata: Mapping[str, object],
    body: str,
    *,
    body_mode: BodyMode = "preserve",
    atomic: bool = True,
) -> None:
    """Write a YAML front matter document."""
    content = render_front_matter_text(metadata, body, body_mode=body_mode)

    if atomic:
        from ledgercore.atomic import atomic_write_text

        atomic_write_text(path, content)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def iter_source_files(
    directory: Path,
    extensions: tuple[str, ...],
    *,
    recursive: bool = True,
) -> list[Path]:
    """Iterate source files matching given extensions in sorted order."""
    if not directory.is_dir():
        return []
    ext_lower = {e.lower() for e in extensions}
    if recursive:
        paths = [
            p
            for p in directory.rglob("*")
            if p.is_file() and p.suffix.lower() in ext_lower
        ]
    else:
        paths = [
            p
            for p in directory.iterdir()
            if p.is_file() and p.suffix.lower() in ext_lower
        ]
    return sorted(paths)


def iter_markdown_files(
    directory: Path,
    *,
    recursive: bool = False,
) -> list[Path]:
    """Iterate markdown files in sorted order."""
    return iter_source_files(directory, (".md",), recursive=recursive)


# Compatibility aliases
read_markdown_front_matter = read_front_matter_document
write_markdown_front_matter = write_front_matter_document
