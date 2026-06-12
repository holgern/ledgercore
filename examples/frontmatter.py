"""Example: working with YAML front matter documents."""

import tempfile
from pathlib import Path

from ledgercore.frontmatter import (
    iter_markdown_files,
    read_front_matter_document,
    write_front_matter_document,
)

# Create a temporary directory for the example
with tempfile.TemporaryDirectory() as tmp:
    records = Path(tmp) / "records"
    records.mkdir()

    # Write a front matter document
    path = records / "task-0001.md"
    write_front_matter_document(
        path,
        {"id": "task-0001", "status": "open", "priority": "high"},
        "# Implement parser\n\nParse input files correctly.\n",
        body_mode="ensure-single-final-newline",
    )

    # Read it back
    metadata, body = read_front_matter_document(path)
    assert metadata["id"] == "task-0001"
    assert metadata["status"] == "open"
    assert body.startswith("# Implement parser")

    # Write another document
    path2 = records / "task-0002.md"
    write_front_matter_document(
        path2,
        {"id": "task-0002", "status": "done"},
        "# Write tests\n",
    )

    # Iterate markdown files
    md_files = iter_markdown_files(records)
    assert len(md_files) == 2
    assert md_files[0].name == "task-0001.md"
    assert md_files[1].name == "task-0002.md"

print("frontmatter example passed")
