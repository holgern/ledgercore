"""Generic error hierarchy for ledgercore."""


class LedgerCoreError(Exception):
    """Base exception for all ledgercore errors."""


class StorageError(LedgerCoreError):
    """Base exception for storage-related errors."""


class AtomicWriteError(StorageError):
    """Raised when an atomic write operation fails."""


class FrontMatterError(StorageError):
    """Raised when front matter parsing or writing fails."""


class JsonStoreError(StorageError):
    """Raised when a JSON store operation fails."""


class PathValidationError(StorageError):
    """Raised when a path fails validation."""


class IdFormatError(LedgerCoreError):
    """Raised when an ID does not match the expected format."""
