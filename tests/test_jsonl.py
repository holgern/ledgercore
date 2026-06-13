"""Tests for ledgercore.jsonl."""

from pathlib import Path

import pytest

from ledgercore.errors import JsonStoreError
from ledgercore.jsonl import load_jsonl_objects, write_jsonl_objects


def test_load_keeps_valid_rows_and_reports_issues(tmp_path: Path) -> None:
    path = tmp_path / "records.jsonl"
    path.write_text(
        '# comment\n\n{"id": 1}\nnot-json\n["array"]\n{"id": 2}\n',
        encoding="utf-8",
    )
    result = load_jsonl_objects(path)
    assert result.rows == [{"id": 1}, {"id": 2}]
    assert [(issue.line, issue.code) for issue in result.issues] == [
        (4, "invalid_json"),
        (5, "non_object"),
    ]


def test_missing_can_return_empty(tmp_path: Path) -> None:
    result = load_jsonl_objects(tmp_path / "missing", missing="empty")
    assert result.rows == []
    assert result.issues == []


def test_missing_strict_raises(tmp_path: Path) -> None:
    with pytest.raises(JsonStoreError):
        load_jsonl_objects(tmp_path / "missing")


def test_write_is_compact_deterministic_and_final_newline(tmp_path: Path) -> None:
    path = tmp_path / "records.jsonl"
    write_jsonl_objects(path, [{"z": 1, "a": "é"}], atomic=False)
    assert path.read_text(encoding="utf-8") == '{"a":"é","z":1}\n'


def test_write_empty_has_no_newline(tmp_path: Path) -> None:
    path = tmp_path / "records.jsonl"
    write_jsonl_objects(path, [])
    assert path.read_text(encoding="utf-8") == ""
