"""Tests for ledgercore.frontmatter."""

from __future__ import annotations

from pathlib import Path

import pytest

from ledgercore.errors import FrontMatterError
from ledgercore.frontmatter import (
    iter_markdown_files,
    iter_source_files,
    read_front_matter_document,
    read_markdown_front_matter,
    write_front_matter_document,
    write_markdown_front_matter,
)


def _write_doc(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestReadFrontMatterDocument:
    def test_valid_front_matter(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.md"
        _write_doc(p, "---\ntitle: Test\n---\nBody here.\n")
        meta, body = read_front_matter_document(p)
        assert meta == {"title": "Test"}
        assert body == "Body here.\n"

    def test_empty_front_matter(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.md"
        _write_doc(p, "---\n---\nBody.\n")
        meta, body = read_front_matter_document(p)
        assert meta == {}
        assert body == "Body.\n"

    def test_closing_at_eof(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.md"
        _write_doc(p, "---\ntitle: End\n---")
        meta, body = read_front_matter_document(p)
        assert meta == {"title": "End"}
        assert body == ""

    def test_normalizes_crlf(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.md"
        p.write_bytes(b"---\r\ntitle: CRLF\r\n---\r\nBody.\r\n")
        meta, body = read_front_matter_document(p)
        assert meta == {"title": "CRLF"}
        assert body == "Body.\n"

    def test_missing_opening_delimiter(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.md"
        _write_doc(p, "title: No\n---\nBody.\n")
        with pytest.raises(FrontMatterError, match="must start with"):
            read_front_matter_document(p)

    def test_missing_closing_delimiter(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.md"
        _write_doc(p, "---\ntitle: No close\n")
        with pytest.raises(FrontMatterError, match="closing"):
            read_front_matter_document(p)

    def test_non_mapping_yaml(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.md"
        _write_doc(p, "---\n- item1\n- item2\n---\nBody.\n")
        with pytest.raises(FrontMatterError, match="mapping"):
            read_front_matter_document(p)


class TestWriteFrontMatterDocument:
    def test_round_trip(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.md"
        meta = {"title": "Test", "count": 5}
        body = "Some body.\n"
        write_front_matter_document(p, meta, body)
        meta2, body2 = read_front_matter_document(p)
        assert meta2 == meta
        assert body2 == body

    def test_body_mode_preserve(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.md"
        write_front_matter_document(p, {}, "body", body_mode="preserve")
        _, body = read_front_matter_document(p)
        assert body == "body"

    def test_body_mode_ensure_single_final_newline(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.md"
        write_front_matter_document(
            p, {}, "body", body_mode="ensure-single-final-newline"
        )
        content = p.read_text(encoding="utf-8")
        assert content.endswith("body\n")
        assert not content.endswith("body\n\n")

    def test_body_mode_ensure_strips_extra_newlines(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.md"
        write_front_matter_document(
            p, {}, "body\n\n", body_mode="ensure-single-final-newline"
        )
        content = p.read_text(encoding="utf-8")
        assert content.count("body\n\n") == 0
        assert content.endswith("body\n")


class TestIterSourceFiles:
    def test_finds_matching_extensions(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("md")
        (tmp_path / "b.adoc").write_text("adoc")
        (tmp_path / "c.txt").write_text("txt")
        result = iter_source_files(tmp_path, (".md", ".adoc"))
        names = [p.name for p in result]
        assert "a.md" in names
        assert "b.adoc" in names
        assert "c.txt" not in names

    def test_case_insensitive(self, tmp_path: Path) -> None:
        (tmp_path / "a.MD").write_text("md")
        result = iter_source_files(tmp_path, (".md",))
        assert len(result) == 1

    def test_sorted(self, tmp_path: Path) -> None:
        (tmp_path / "z.md").write_text("z")
        (tmp_path / "a.md").write_text("a")
        result = iter_source_files(tmp_path, (".md",))
        assert result[0].name == "a.md"

    def test_recursive(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "a.md").write_text("a")
        result = iter_source_files(tmp_path, (".md",), recursive=True)
        assert len(result) == 1

    def test_non_recursive(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "a.md").write_text("a")
        (tmp_path / "b.md").write_text("b")
        result = iter_source_files(tmp_path, (".md",), recursive=False)
        assert len(result) == 1
        assert result[0].name == "b.md"

    def test_missing_directory(self, tmp_path: Path) -> None:
        result = iter_source_files(tmp_path / "nope", (".md",))
        assert result == []


    def test_finds_md_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        result = iter_markdown_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "a.md"


class TestAdocFrontMatter:
    def test_adoc_round_trip(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.adoc"
        meta = {"title": "Architecture", "status": "draft"}
        body = "== Section 1\n\nSome content.\n"
        write_front_matter_document(p, meta, body)
        meta2, body2 = read_front_matter_document(p)
        assert meta2 == meta
        assert body2 == body

    def test_adoc_empty_front_matter(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.adoc"
        _write_doc(p, "---\n---\nAsciiDoc body.\n")
        meta, body = read_front_matter_document(p)
        assert meta == {}
        assert body == "AsciiDoc body.\n"


class TestCompatibilityAliases:
    def test_read_markdown_front_matter(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.md"
        _write_doc(p, "---\ntitle: Alias\n---\nBody.\n")
        meta, body = read_markdown_front_matter(p)
        assert meta == {"title": "Alias"}
        assert body == "Body.\n"

    def test_write_markdown_front_matter(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.md"
        write_markdown_front_matter(p, {"key": 1}, "body\n")
        meta, body = read_front_matter_document(p)
        assert meta == {"key": 1}
        assert body == "body\n"
