"""Example: working with atomic writes, JSON, YAML, and path helpers."""

import tempfile
from pathlib import Path

from ledgercore.atomic import atomic_create_text, atomic_write_text
from ledgercore.errors import AtomicWriteError
from ledgercore.jsonio import load_json_object, write_json
from ledgercore.paths import (
    locate_config,
    resolve_config_relative_path,
    validate_relative_posix_path,
)
from ledgercore.yamlio import load_yaml_object, write_yaml

# Create a temporary directory for the example
with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)

    # --- Atomic writes ---
    target = base / "hello.txt"
    atomic_write_text(target, "Hello, world!\n")
    assert target.read_text() == "Hello, world!\n"

    # atomic_create_text fails if file exists
    try:
        atomic_create_text(target, "overwrite\n")
        raise AssertionError("Should have raised AtomicWriteError")
    except AtomicWriteError:
        pass

    # atomic_write_text replaces existing files
    atomic_write_text(target, "Updated!\n")
    assert target.read_text() == "Updated!\n"

    # --- JSON store ---
    json_path = base / "state.json"
    write_json(json_path, {"next_id": 5, "active": True})
    state = load_json_object(json_path)
    assert state["next_id"] == 5

    # --- YAML store ---
    yaml_path = base / "config.yaml"
    write_yaml(yaml_path, {"records_dir": "records", "format": "md"}, sort_keys=True)
    config = load_yaml_object(yaml_path)
    assert config["records_dir"] == "records"

    # --- Path validation ---
    validate_relative_posix_path("records/task-0001.md")

    # --- Config discovery ---
    config_file = base / "ledger.toml"
    config_file.write_text("[tool]\n", encoding="utf-8")
    locator = locate_config(base, ("ledger.toml",))
    assert locator is not None
    assert locator.source == "found"

    records_dir = resolve_config_relative_path(
        locator.config_path,
        "records",
        field_name="records_dir",
    )
    assert records_dir.name == "records"

print("storage example passed")
