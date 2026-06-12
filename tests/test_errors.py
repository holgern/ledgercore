"""Tests for ledgercore.errors."""

from __future__ import annotations

from ledgercore.errors import (
    AtomicWriteError,
    FrontMatterError,
    IdFormatError,
    JsonStoreError,
    LedgerCoreError,
    PathValidationError,
    StorageError,
    YamlStoreError,
)


class TestLedgerCoreError:
    def test_default_code(self) -> None:
        err = LedgerCoreError("test")
        assert err.code == "LEDGERCORE_ERROR"
        assert str(err) == "test"

    def test_custom_code(self) -> None:
        err = LedgerCoreError("test", code="CUSTOM_ERROR")
        assert err.code == "CUSTOM_ERROR"

    def test_subclass_inherits_code(self) -> None:
        err = AtomicWriteError("write failed")
        assert isinstance(err, StorageError)
        assert isinstance(err, LedgerCoreError)

    def test_all_errors_are_ledgercore_errors(self) -> None:
        errors = [
            AtomicWriteError("a"),
            FrontMatterError("b"),
            JsonStoreError("c"),
            YamlStoreError("d"),
            PathValidationError("e"),
            IdFormatError("f"),
            StorageError("g"),
        ]
        for err in errors:
            assert isinstance(err, LedgerCoreError)
