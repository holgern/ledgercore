#!/usr/bin/env python3
"""Release smoke test for a built ledgercore wheel.

Run after ``python -m build`` from the repository root, in a Python
environment where the built wheel has been installed (for example a clean
virtualenv):

    python -m venv .smoke
    .smoke/bin/python -m pip install dist/*.whl
    .smoke/bin/python scripts/smoke_wheel.py

The script exercises a representative slice of the public API so that
packaging regressions (missing modules, lost data files, broken imports)
surface before publishing. It is intentionally dependency-free beyond
ledgercore itself.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from ledgercore import __version__
from ledgercore.errors import IdFormatError
from ledgercore.frontmatter import render_front_matter_text, split_front_matter_text
from ledgercore.ids import LedgerIdFormat
from ledgercore.jsonl import load_jsonl_object_map, write_jsonl_objects
from ledgercore.refs import parse_resource_ref
from ledgercore.time import utc_now_iso


def main() -> int:
    # Version is exposed at runtime via the build-generated _version.py.
    assert isinstance(__version__, str) and __version__, __version__

    fmt = LedgerIdFormat(prefix="task")
    assert fmt.format(1) == "task-0001"
    assert fmt.parse("task-0001") == 1
    assert fmt.is_valid("task-0001")
    assert not fmt.is_valid("task-0000")

    ref = parse_resource_ref("tl:task-0001")
    assert ref.global_ref == "tl:task-0001"
    try:
        parse_resource_ref("tl:task-0000")
    except IdFormatError:
        pass
    else:  # pragma: no cover - defensive
        raise AssertionError("tl:task-0000 should be rejected")

    # Minimal front matter must round-trip YAML-significant scalars safely.
    hazards = ["- item", "*alias", "~", "no", "2026-06-13"]
    text = render_front_matter_text(
        {"id": "task-0001", "flags": hazards},
        "# Body\n",
        scalar_style="minimal",
    )
    meta, body = split_front_matter_text(text, preserve_yaml_timestamps_as_strings=True)
    assert meta["id"] == "task-0001"
    assert meta["flags"] == hazards
    assert body == "# Body\n"

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "rows.jsonl"
        write_jsonl_objects(path, [{"id": "a", "v": 1}, {"id": "b", "v": 2}])
        result = load_jsonl_object_map(path, key="id")
        assert not result.issues
        assert set(result.rows_by_key) == {"a", "b"}

    assert utc_now_iso().endswith("Z")

    print(f"ledgercore {__version__} smoke test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
