"""Cross-ledger resource reference parsing and formatting."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from ledgercore.errors import IdFormatError

RefStyle = Literal["canonical", "file", "local"]

_TOKEN_RE = re.compile(r"^[a-z][a-z0-9]*$")
_KIND_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_CANONICAL_RE = re.compile(
    r"^(?P<ledger>[A-Za-z][A-Za-z0-9]*):"
    r"(?P<kind>[A-Za-z][A-Za-z0-9_-]*)-"
    r"(?P<number>\d+)$"
)
_LOCAL_RE = re.compile(r"^(?P<kind>[A-Za-z][A-Za-z0-9_-]*)-(?P<number>\d+)$")
_LEGACY_RE = re.compile(
    r"^(?P<ledger>[A-Za-z][A-Za-z0-9]*)_"
    r"(?P<kind>[A-Za-z][A-Za-z0-9_-]*)_"
    r"(?P<number>\d+)$"
)


@dataclass(frozen=True)
class LedgerResourceRef:
    """A ledger-neutral reference to a numeric resource record.

    Canonical global form:
        tl:task-0001

    File-safe global form:
        tl-task-0001

    Local form:
        task-0001
    """

    ledger: str | None
    kind: str
    number: int
    width: int = 4

    def __post_init__(self) -> None:
        if self.ledger is not None:
            object.__setattr__(
                self,
                "ledger",
                normalize_ref_token(self.ledger, label="ledger"),
            )
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        _validate_number(self.number)
        if self.width <= 0:
            raise IdFormatError("Width must be positive")

    @property
    def local_id(self) -> str:
        return f"{self.kind}-{self.number:0{self.width}d}"

    @property
    def is_global(self) -> bool:
        return self.ledger is not None

    @property
    def global_ref(self) -> str:
        if self.ledger is None:
            raise IdFormatError("Cannot format a global ref without a ledger code")
        return f"{self.ledger}:{self.local_id}"

    @property
    def file_ref(self) -> str:
        if self.ledger is None:
            raise IdFormatError("Cannot format a file ref without a ledger code")
        return f"{self.ledger}-{self.local_id}"

    def format(self, style: RefStyle = "canonical") -> str:
        if style == "canonical":
            return self.global_ref
        if style == "file":
            return self.file_ref
        if style == "local":
            return self.local_id
        raise IdFormatError(f"Unsupported ref style: {style}")

    def with_ledger(self, ledger: str) -> LedgerResourceRef:
        return LedgerResourceRef(
            ledger=ledger,
            kind=self.kind,
            number=self.number,
            width=self.width,
        )


def normalize_ref_token(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if not _TOKEN_RE.fullmatch(normalized):
        raise IdFormatError(f"Invalid {label}: {value!r}")
    return normalized


def normalize_kind(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    if not _KIND_RE.fullmatch(normalized):
        raise IdFormatError(f"Invalid resource kind: {value!r}")
    return normalized


def parse_resource_ref(
    value: str,
    *,
    default_ledger: str | None = None,
    width: int = 4,
    allow_file_alias: bool = True,
    allow_legacy_alias: bool = True,
    allowed_ledgers: set[str] | None = None,
    allowed_kinds: set[str] | None = None,
) -> LedgerResourceRef:
    """Parse a canonical, file-safe, legacy, or local resource reference.

    Accepted input examples:
        tl:task-0001      canonical global ref
        tl-task-0001      file-safe alias
        TL-TASK-0001      uppercase file-safe alias
        al_adr_0046       legacy underscore alias
        task-0001         local ref, only globalized if default_ledger is provided

    Canonical output is always available through `.global_ref` when ledger is set.
    """
    if not isinstance(value, str):
        raise IdFormatError("Resource ref must be a string")
    raw = value.strip()
    if not raw:
        raise IdFormatError("Resource ref must not be empty")

    ref: LedgerResourceRef | None = None

    m = _CANONICAL_RE.fullmatch(raw)
    if m is not None:
        ref = _build_ref(
            m.group("ledger"),
            m.group("kind"),
            m.group("number"),
            width=width,
        )

    if ref is None and allow_legacy_alias:
        m = _LEGACY_RE.fullmatch(raw)
        if m is not None:
            ref = _build_ref(
                m.group("ledger"),
                m.group("kind"),
                m.group("number"),
                width=width,
            )

    if ref is None and allow_file_alias:
        ref = _parse_file_alias(raw, width=width)

    if ref is None:
        m = _LOCAL_RE.fullmatch(raw)
        if m is not None:
            ledger = default_ledger
            ref = _build_ref(ledger, m.group("kind"), m.group("number"), width=width)

    if ref is None:
        raise IdFormatError(f"Invalid resource ref: {value!r}")

    _check_allowed(ref, allowed_ledgers=allowed_ledgers, allowed_kinds=allowed_kinds)
    return ref


def parse_global_ref(value: str, **kwargs: object) -> LedgerResourceRef:
    """Parse and require a ledger namespace."""
    ref = parse_resource_ref(value, **kwargs)  # type: ignore[arg-type]
    if ref.ledger is None:
        raise IdFormatError(f"Resource ref is local, not global: {value!r}")
    return ref


def parse_local_ref(value: str, *, width: int = 4) -> LedgerResourceRef:
    """Parse a local kind-number ID without assigning a ledger."""
    ref = parse_resource_ref(
        value,
        width=width,
        allow_file_alias=False,
        allow_legacy_alias=False,
    )
    if ref.ledger is not None:
        raise IdFormatError(f"Resource ref is global, not local: {value!r}")
    return ref


def is_resource_ref(value: object, **kwargs: object) -> bool:
    """Return True if value is a valid resource ref."""
    if not isinstance(value, str):
        return False
    try:
        parse_resource_ref(value, **kwargs)  # type: ignore[arg-type]
    except IdFormatError:
        return False
    return True


def _parse_file_alias(value: str, *, width: int) -> LedgerResourceRef | None:
    parts = value.split("-")
    if len(parts) < 3:
        return None
    ledger = parts[0]
    number_text = parts[-1]
    kind = "-".join(parts[1:-1])
    if not number_text.isdigit():
        return None
    try:
        return _build_ref(ledger, kind, number_text, width=width)
    except IdFormatError:
        return None


def _build_ref(
    ledger: str | None,
    kind: str,
    number_text: str,
    *,
    width: int,
) -> LedgerResourceRef:
    if not number_text.isdigit():
        raise IdFormatError(f"Invalid resource number: {number_text!r}")
    number = int(number_text)
    resolved_width = max(width, len(number_text))
    return LedgerResourceRef(
        ledger=ledger,
        kind=kind,
        number=number,
        width=resolved_width,
    )


def _validate_number(number: int) -> None:
    if isinstance(number, bool):
        raise IdFormatError("Number must not be a boolean")
    if number <= 0:
        raise IdFormatError(f"Number must be positive, got {number}")


def _check_allowed(
    ref: LedgerResourceRef,
    *,
    allowed_ledgers: set[str] | None,
    allowed_kinds: set[str] | None,
) -> None:
    if allowed_ledgers is not None:
        normalized_ledgers = {
            normalize_ref_token(item, label="ledger") for item in allowed_ledgers
        }
        if ref.ledger is not None and ref.ledger not in normalized_ledgers:
            raise IdFormatError(f"Ledger code is not allowed: {ref.ledger}")
    if allowed_kinds is not None:
        normalized_kinds = {normalize_kind(item) for item in allowed_kinds}
        if ref.kind not in normalized_kinds:
            raise IdFormatError(f"Resource kind is not allowed: {ref.kind}")
