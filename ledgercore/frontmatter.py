"""YAML front matter read/write and file iteration for ledgercore."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

from ledgercore.errors import FrontMatterError

MissingFrontMatterMode = Literal["error", "empty"]
BodyMode = Literal["preserve", "ensure-single-final-newline", "strip-leading-blank"]
ScalarStyle = Literal["minimal", "pyyaml"]
RemainingKeyOrder = Literal["input", "sorted"]
EmptyStringStyle = Literal["single", "double"]
TemplatePlaceholderMode = bool | Literal["none", "whole-value", "anywhere"]


@dataclass(frozen=True)
class FrontMatterRenderOptions:
    """Options controlling front matter rendering."""

    key_order: tuple[str, ...] = ()
    remaining_key_order: RemainingKeyOrder = "input"
    body_mode: BodyMode = "preserve"
    scalar_style: ScalarStyle = "pyyaml"
    sequence_indent: str = ""
    empty_string_style: EmptyStringStyle = "single"
    quote_boolish_strings: bool = True
    quote_special_strings: bool = True


_FRONT_MATTER_DELIM = "---"
_SAFE_MINIMAL_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
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


def _quote_template_values_anywhere(yaml_block: str) -> str:
    lines: list[str] = []
    for line in yaml_block.splitlines(keepends=True):
        content = line.removesuffix("\n")
        newline = "\n" if line.endswith("\n") else ""
        stripped = content.lstrip()
        if not stripped or stripped.startswith(("#", "-")) or ":" not in content:
            lines.append(line)
            continue
        prefix, value = content.split(":", 1)
        scalar = value.strip()
        if (
            "{{" not in scalar
            or "}}" not in scalar
            or scalar.startswith(("'", '"', "|", ">"))
        ):
            lines.append(line)
            continue
        leading = value[: len(value) - len(value.lstrip())]
        escaped = scalar.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'{prefix}:{leading}"{escaped}"{newline}')
    return "".join(lines)


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
    quote_template_placeholders: TemplatePlaceholderMode = False,
) -> tuple[dict[str, object], str]:
    """Split YAML front matter from an in-memory document."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith(_FRONT_MATTER_DELIM + "\n"):
        if missing == "empty":
            return {}, text
        raise FrontMatterError("Document must start with '---' followed by a newline")

    yaml_block, body = _split_document(normalized)
    if not yaml_block.strip():
        return {}, body
    if quote_template_placeholders in (True, "whole-value"):
        yaml_block = _quote_template_values(yaml_block)
    elif quote_template_placeholders == "anywhere":
        yaml_block = _quote_template_values_anywhere(yaml_block)
    elif quote_template_placeholders not in (False, "none"):
        raise ValueError(
            f"Unsupported template placeholder mode: {quote_template_placeholders}"
        )

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
            f"YAML front matter must be a mapping, got {type(loaded).__name__}"
        )
    return dict(loaded), body


def _ordered_keys(
    metadata: Mapping[str, object],
    key_order: Sequence[str],
    remaining_key_order: RemainingKeyOrder,
) -> list[str]:
    ordered = [key for key in key_order if key in metadata]
    ordered_set = set(ordered)
    remaining = [key for key in metadata if key not in ordered_set]
    if remaining_key_order == "sorted":
        remaining.sort()
    elif remaining_key_order != "input":
        raise ValueError(f"Unsupported remaining key order: {remaining_key_order}")
    return ordered + remaining


_BOOLISH_STRINGS = {
    "true",
    "false",
    "null",
    "none",
    "yes",
    "no",
    "on",
    "off",
}

# YAML scalar tokens that some loaders coerce to None.
_NULLISH_STRINGS = {"null", "none", "~"}

# Conservative safe plain scalar: alphanumeric lead character followed by a
# restricted middle set. This intentionally excludes YAML plain-scalar
# hazards (indicator lead characters, colons, hashes, quotes, brackets,
# braces, and other reserved indicators) so that any string outside this
# set is quoted. Quoting more than strictly necessary is deterministic and
# safe; the goal of the minimal renderer is round-trip fidelity, not the
# shortest possible representation.
_SAFE_PLAIN_SCALAR_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _./-]*$")


def _quote_minimal_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _render_minimal_scalar(
    value: object,
    *,
    empty_string_style: EmptyStringStyle,
    quote_boolish_strings: bool,
    quote_special_strings: bool,
) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if not isinstance(value, str):
        raise FrontMatterError(
            "Minimal front matter supports only strings, booleans, integers, "
            "null, and flat sequences; use scalar_style='pyyaml' for nested "
            "or other values"
        )
    if not value:
        if empty_string_style == "single":
            return "''"
        if empty_string_style == "double":
            return '""'
        raise ValueError(f"Unsupported empty string style: {empty_string_style}")
    folded = value.casefold()
    boolish = folded in _BOOLISH_STRINGS
    nullish = folded in _NULLISH_STRINGS
    special = (
        value != value.strip()
        or any(char in value for char in ':#[]{}\n"\\')
        or _SAFE_PLAIN_SCALAR_RE.fullmatch(value) is None
    )
    if (
        (quote_boolish_strings and boolish)
        or nullish
        or (quote_special_strings and special)
    ):
        return _quote_minimal_string(value)
    return value


def _render_minimal_yaml(
    metadata: Mapping[str, object],
    keys: Sequence[str],
    *,
    sequence_indent: str,
    empty_string_style: EmptyStringStyle,
    quote_boolish_strings: bool,
    quote_special_strings: bool,
) -> str:
    lines: list[str] = []
    for key in keys:
        if not _SAFE_MINIMAL_KEY.fullmatch(key):
            raise FrontMatterError(
                f"Minimal scalar style requires a safe metadata key, got {key!r}"
            )
        value = metadata[key]
        if isinstance(value, Mapping):
            raise FrontMatterError(
                "Minimal front matter does not support nested mappings; "
                "use scalar_style='pyyaml'"
            )
        if isinstance(value, (list, tuple)):
            if not value:
                lines.append(f"{key}: []")
                continue
            lines.append(f"{key}:")
            for item in value:
                if isinstance(item, (Mapping, list, tuple)):
                    raise FrontMatterError(
                        "Minimal front matter does not support nested "
                        "sequences; use scalar_style='pyyaml'"
                    )
                rendered = _render_minimal_scalar(
                    item,
                    empty_string_style=empty_string_style,
                    quote_boolish_strings=quote_boolish_strings,
                    quote_special_strings=quote_special_strings,
                )
                lines.append(f"{sequence_indent}- {rendered}")
            continue
        rendered = _render_minimal_scalar(
            value,
            empty_string_style=empty_string_style,
            quote_boolish_strings=quote_boolish_strings,
            quote_special_strings=quote_special_strings,
        )
        lines.append(f"{key}: {rendered}")
    return "\n".join(lines) + "\n"


def render_front_matter_text(
    metadata: Mapping[str, object],
    body: str = "",
    *,
    key_order: Sequence[str] = (),
    body_mode: BodyMode = "preserve",
    scalar_style: ScalarStyle = "pyyaml",
    render_options: FrontMatterRenderOptions | None = None,
    remaining_key_order: RemainingKeyOrder = "input",
    sequence_indent: str = "",
    empty_string_style: EmptyStringStyle = "single",
    quote_boolish_strings: bool = True,
    quote_special_strings: bool = True,
) -> str:
    """Render metadata and body as a YAML front matter document."""
    if render_options is not None:
        key_order = render_options.key_order
        remaining_key_order = render_options.remaining_key_order
        body_mode = render_options.body_mode
        scalar_style = render_options.scalar_style
        sequence_indent = render_options.sequence_indent
        empty_string_style = render_options.empty_string_style
        quote_boolish_strings = render_options.quote_boolish_strings
        quote_special_strings = render_options.quote_special_strings
    if body_mode == "ensure-single-final-newline":
        body = body.rstrip("\n") + "\n" if body else body
    elif body_mode == "strip-leading-blank":
        body = body.lstrip("\n")
    elif body_mode != "preserve":
        raise ValueError(f"Unsupported body mode: {body_mode}")
    if scalar_style not in ("minimal", "pyyaml"):
        raise ValueError(f"Unsupported scalar style: {scalar_style}")

    keys = _ordered_keys(metadata, key_order, remaining_key_order)
    if scalar_style == "minimal":
        yaml_block = _render_minimal_yaml(
            metadata,
            keys,
            sequence_indent=sequence_indent,
            empty_string_style=empty_string_style,
            quote_boolish_strings=quote_boolish_strings,
            quote_special_strings=quote_special_strings,
        )
    else:
        ordered_metadata = {key: metadata[key] for key in keys}
        yaml_block = yaml.safe_dump(
            ordered_metadata,
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
    quote_template_placeholders: TemplatePlaceholderMode = False,
    body_mode: BodyMode = "preserve",
    scalar_style: ScalarStyle = "pyyaml",
    remaining_key_order: RemainingKeyOrder = "input",
    sequence_indent: str = "",
    empty_string_style: EmptyStringStyle = "single",
    quote_boolish_strings: bool = True,
    quote_special_strings: bool = True,
    render_options: FrontMatterRenderOptions | None = None,
) -> str:
    """Update metadata in an in-memory front matter document."""
    metadata, body = split_front_matter_text(
        text,
        missing=missing,
        preserve_yaml_timestamps_as_strings=preserve_yaml_timestamps_as_strings,
        quote_template_placeholders=quote_template_placeholders,
    )
    metadata.update(updates)
    return render_front_matter_text(
        metadata,
        body,
        key_order=key_order,
        body_mode=body_mode,
        scalar_style=scalar_style,
        remaining_key_order=remaining_key_order,
        sequence_indent=sequence_indent,
        empty_string_style=empty_string_style,
        quote_boolish_strings=quote_boolish_strings,
        quote_special_strings=quote_special_strings,
        render_options=render_options,
    )


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
    key_order: Sequence[str] = (),
    scalar_style: ScalarStyle = "pyyaml",
    remaining_key_order: RemainingKeyOrder = "input",
    sequence_indent: str = "",
    empty_string_style: EmptyStringStyle = "single",
    quote_boolish_strings: bool = True,
    quote_special_strings: bool = True,
    render_options: FrontMatterRenderOptions | None = None,
) -> None:
    """Write a YAML front matter document."""
    content = render_front_matter_text(
        metadata,
        body,
        key_order=key_order,
        body_mode=body_mode,
        scalar_style=scalar_style,
        remaining_key_order=remaining_key_order,
        sequence_indent=sequence_indent,
        empty_string_style=empty_string_style,
        quote_boolish_strings=quote_boolish_strings,
        quote_special_strings=quote_special_strings,
        render_options=render_options,
    )

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
