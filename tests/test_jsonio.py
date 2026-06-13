"""Tests for ledgercore.jsonio."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ledgercore.errors import JsonStoreError
from ledgercore.jsonio import (
    canonical_json,
    dumps_json,
    load_json_array,
    load_json_object,
    write_json,
)


def test_canonical_json_is_compact_sorted_and_unicode() -> None:
    assert canonical_json({"z": 1, "a": "é"}) == '{"a":"é","z":1}'


class TestLoadJsonObject:
    def test_loads_object(self, tmp_path: Path) -> None:
        p = tmp_path / "f.json"
        p.write_text('{"a": 1}', encoding="utf-8")
        result = load_json_object(p)
        assert result == {"a": 1}

    def test_rejects_array(self, tmp_path: Path) -> None:
        p = tmp_path / "f.json"
        p.write_text("[1, 2]", encoding="utf-8")
        with pytest.raises(JsonStoreError, match="JSON object"):
            load_json_object(p)

    def test_rejects_invalid_json(self, tmp_path: Path) -> None:
        p = tmp_path / "f.json"
        p.write_text("not json", encoding="utf-8")
        with pytest.raises(JsonStoreError, match="Invalid JSON"):
            load_json_object(p)

    def test_rejects_missing_file(self, tmp_path: Path) -> None:
        p = tmp_path / "missing.json"
        with pytest.raises(JsonStoreError, match="Cannot read"):
            load_json_object(p)

    def test_custom_label(self, tmp_path: Path) -> None:
        p = tmp_path / "f.json"
        p.write_text("[1]", encoding="utf-8")
        with pytest.raises(JsonStoreError, match="my-config"):
            load_json_object(p, label="my-config")

    def test_missing_empty_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / "missing.json"
        result = load_json_object(p, missing="empty")
        assert result == {}

    def test_empty_file_error(self, tmp_path: Path) -> None:
        p = tmp_path / "f.json"
        p.write_text("", encoding="utf-8")
        with pytest.raises(JsonStoreError, match="empty"):
            load_json_object(p, empty="error")

    def test_empty_file_empty_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / "f.json"
        p.write_text("", encoding="utf-8")
        result = load_json_object(p, empty="empty")
        assert result == {}


class TestLoadJsonArray:
    def test_loads_array(self, tmp_path: Path) -> None:
        p = tmp_path / "f.json"
        p.write_text("[1, 2]", encoding="utf-8")
        result = load_json_array(p)
        assert result == [1, 2]

    def test_rejects_object(self, tmp_path: Path) -> None:
        p = tmp_path / "f.json"
        p.write_text('{"a": 1}', encoding="utf-8")
        with pytest.raises(JsonStoreError, match="JSON array"):
            load_json_array(p)

    def test_missing_empty_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / "missing.json"
        result = load_json_array(p, missing="empty")
        assert result == []

    def test_empty_file_empty_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / "f.json"
        p.write_text("", encoding="utf-8")
        result = load_json_array(p, empty="empty")
        assert result == []

    def test_empty_file_error(self, tmp_path: Path) -> None:
        p = tmp_path / "f.json"
        p.write_text("", encoding="utf-8")
        with pytest.raises(JsonStoreError, match="empty"):
            load_json_array(p, empty="error")


class TestWriteJson:
    def test_dumps_defaults_match_write_contract(self) -> None:
        assert dumps_json({"b": 1, "a": 2}) == (
            '{\n  "a": 2,\n  "b": 1\n}\n'
        )

    def test_dumps_can_omit_final_newline(self) -> None:
        assert dumps_json(
            {"b": 1, "a": 2}, final_newline=False
        ) == '{\n  "a": 2,\n  "b": 1\n}'

    def test_write_compact(self, tmp_path: Path) -> None:
        path = tmp_path / "compact.json"
        write_json(path, {"b": 1, "a": 2}, compact=True)
        assert path.read_text(encoding="utf-8") == '{"a":2,"b":1}\n'

    def test_writes_deterministic(self, tmp_path: Path) -> None:
        p = tmp_path / "f.json"
        write_json(p, {"b": 2, "a": 1})
        text = p.read_text(encoding="utf-8")
        data = json.loads(text)
        assert data == {"a": 1, "b": 2}
        lines = text.split("\n")
        assert lines[1].startswith('  "a"')

    def test_indent_and_sort(self, tmp_path: Path) -> None:
        p = tmp_path / "f.json"
        write_json(p, {"z": 1, "a": 2})
        text = p.read_text(encoding="utf-8")
        assert '"a"' in text
        assert text.index('"a"') < text.index('"z"')

    def test_final_newline(self, tmp_path: Path) -> None:
        p = tmp_path / "f.json"
        write_json(p, {"x": 1})
        assert p.read_text(encoding="utf-8").endswith("\n")

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        p = tmp_path / "sub" / "f.json"
        write_json(p, {})
        assert p.exists()
