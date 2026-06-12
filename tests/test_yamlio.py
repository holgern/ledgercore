"""Tests for ledgercore.yamlio."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ledgercore.errors import YamlStoreError
from ledgercore.yamlio import load_yaml_object, write_yaml


class TestLoadYamlObject:
    def test_loads_mapping(self, tmp_path: Path) -> None:
        p = tmp_path / "f.yaml"
        p.write_text("key: value\n", encoding="utf-8")
        result = load_yaml_object(p)
        assert result == {"key": "value"}

    def test_empty_mapping(self, tmp_path: Path) -> None:
        p = tmp_path / "f.yaml"
        p.write_text("{}\n", encoding="utf-8")
        result = load_yaml_object(p)
        assert result == {}

    def test_empty_yaml_returns_empty_dict(self, tmp_path: Path) -> None:
        p = tmp_path / "f.yaml"
        p.write_text("---\n...\n", encoding="utf-8")
        result = load_yaml_object(p)
        assert result == {}

    def test_rejects_non_mapping(self, tmp_path: Path) -> None:
        p = tmp_path / "f.yaml"
        p.write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(YamlStoreError, match="mapping"):
            load_yaml_object(p)

    def test_rejects_invalid_yaml(self, tmp_path: Path) -> None:
        p = tmp_path / "f.yaml"
        p.write_text("{{{{invalid\n", encoding="utf-8")
        with pytest.raises(YamlStoreError, match="Invalid YAML"):
            load_yaml_object(p)

    def test_missing_error(self, tmp_path: Path) -> None:
        p = tmp_path / "missing.yaml"
        with pytest.raises(YamlStoreError, match="Cannot read"):
            load_yaml_object(p)

    def test_missing_empty_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / "missing.yaml"
        result = load_yaml_object(p, missing="empty")
        assert result == {}

    def test_empty_file_error(self, tmp_path: Path) -> None:
        p = tmp_path / "f.yaml"
        p.write_text("", encoding="utf-8")
        with pytest.raises(YamlStoreError, match="empty"):
            load_yaml_object(p, empty="error")

    def test_empty_file_default_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / "f.yaml"
        p.write_text("", encoding="utf-8")
        result = load_yaml_object(p)
        assert result == {}

    def test_custom_label(self, tmp_path: Path) -> None:
        p = tmp_path / "f.yaml"
        p.write_text("[1]\n", encoding="utf-8")
        with pytest.raises(YamlStoreError, match="my-config"):
            load_yaml_object(p, label="my-config")


class TestWriteYaml:
    def test_writes_yaml(self, tmp_path: Path) -> None:
        p = tmp_path / "f.yaml"
        write_yaml(p, {"key": "value"})
        text = p.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        assert data == {"key": "value"}

    def test_final_newline(self, tmp_path: Path) -> None:
        p = tmp_path / "f.yaml"
        write_yaml(p, {"a": 1})
        assert p.read_text(encoding="utf-8").endswith("\n")

    def test_deterministic_sorted(self, tmp_path: Path) -> None:
        p = tmp_path / "f.yaml"
        write_yaml(p, {"z": 1, "a": 2}, sort_keys=True)
        text = p.read_text(encoding="utf-8")
        assert text.index("a:") < text.index("z:")

    def test_no_sort_keys(self, tmp_path: Path) -> None:
        p = tmp_path / "f.yaml"
        write_yaml(p, {"z": 1, "a": 2}, sort_keys=False)
        text = p.read_text(encoding="utf-8")
        # Insertion order should be preserved
        assert text.index("z:") < text.index("a:")

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        p = tmp_path / "sub" / "f.yaml"
        write_yaml(p, {})
        assert p.exists()

    def test_non_atomic(self, tmp_path: Path) -> None:
        p = tmp_path / "f.yaml"
        write_yaml(p, {"a": 1}, atomic=False)
        assert p.read_text(encoding="utf-8").startswith("a:")

    def test_round_trip(self, tmp_path: Path) -> None:
        p = tmp_path / "f.yaml"
        data = {"title": "Test", "count": 5, "items": ["a", "b"]}
        write_yaml(p, data)
        result = load_yaml_object(p)
        assert result == data
