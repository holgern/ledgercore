"""Generic error hierarchy for ledgercore."""


class LedgerCoreError(Exception):
    """Base exception for all ledgercore errors."""

    code: str = "LEDGERCORE_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class StorageError(LedgerCoreError):
    """Base exception for storage-related errors."""


class AtomicWriteError(StorageError):
    """Raised when an atomic write operation fails."""


class FrontMatterError(StorageError):
    """Raised when front matter parsing or writing fails."""


class JsonStoreError(StorageError):
    """Raised when a JSON store operation fails."""


class YamlStoreError(StorageError):
    """Raised when a YAML store operation fails."""


class PathValidationError(StorageError):
    """Raised when a path fails validation."""


class IdFormatError(LedgerCoreError):
    """Raised when an ID does not match the expected format."""
