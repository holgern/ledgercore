"""Tests for ledgercore.jsonio."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ledgercore.errors import JsonStoreError
from ledgercore.jsonio import load_json_array, load_json_object, write_json


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


class TestWriteJson:
    def test_writes_deterministic(self, tmp_path: Path) -> None:
        p = tmp_path / "f.json"
        write_json(p, {"b": 2, "a": 1})
        text = p.read_text(encoding="utf-8")
        data = json.loads(text)
        assert data == {"a": 1, "b": 2}
        lines = text.split("\n")
        assert lines[1].startswith("  \"a\"")

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
