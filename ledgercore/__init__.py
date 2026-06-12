"""ledgercore: generic ledger and storage primitives."""

from ledgercore.atomic import atomic_create_text, atomic_write_text
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
from ledgercore.frontmatter import (
    iter_markdown_files,
    iter_source_files,
    read_front_matter_document,
    write_front_matter_document,
)
from ledgercore.ids import (
    LedgerIdFormat,
    LedgerIdParts,
    NumericIdFormat,
    next_prefixed_id,
    parse_prefixed_number,
    slugify_ref,
)
from ledgercore.refs import (
    LedgerResourceRef,
    RefStyle,
    is_resource_ref,
    normalize_kind,
    normalize_ref_token,
    parse_global_ref,
    parse_local_ref,
    parse_resource_ref,
)
from ledgercore.io import (
    content_hash,
    ensure_dir,
    merge_text,
    normalize_newlines,
    read_text,
    summarize_text,
    write_text,
)
from ledgercore.jsonio import load_json_array, load_json_object, write_json
from ledgercore.paths import (
    ConfigLocator,
    find_config_upwards,
    is_relative_to,
    locate_config,
    resolve_config_relative_path,
    resolve_relative_child,
    validate_relative_posix_path,
)
from ledgercore.time import utc_now_iso
from ledgercore.yamlio import load_yaml_object, write_yaml

__all__ = [
    "atomic_create_text",
    "atomic_write_text",
    "AtomicWriteError",
    "FrontMatterError",
    "IdFormatError",
    "JsonStoreError",
    "LedgerCoreError",
    "PathValidationError",
    "StorageError",
    "YamlStoreError",
    "iter_markdown_files",
    "iter_source_files",
    "read_front_matter_document",
    "write_front_matter_document",
    "LedgerIdFormat",
    "LedgerIdParts",
    "NumericIdFormat",
    "next_prefixed_id",
    "parse_prefixed_number",
    "slugify_ref",
    "LedgerResourceRef",
    "RefStyle",
    "is_resource_ref",
    "normalize_kind",
    "normalize_ref_token",
    "parse_global_ref",
    "parse_local_ref",
    "parse_resource_ref",
    "content_hash",
    "ensure_dir",
    "merge_text",
    "normalize_newlines",
    "read_text",
    "summarize_text",
    "write_text",
    "load_json_array",
    "load_json_object",
    "write_json",
    "ConfigLocator",
    "find_config_upwards",
    "is_relative_to",
    "locate_config",
    "resolve_config_relative_path",
    "resolve_relative_child",
    "validate_relative_posix_path",
    "utc_now_iso",
    "load_yaml_object",
    "write_yaml",
]
