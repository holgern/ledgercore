"""Tests for ledgercore.frontmatter."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from ledgercore.errors import FrontMatterError
from ledgercore.frontmatter import (
    FrontMatterRenderOptions,
    iter_markdown_files,
    iter_source_files,
    read_front_matter_document,
    read_markdown_front_matter,
    render_front_matter_text,
    split_front_matter_text,
    update_front_matter_text,
    write_front_matter_document,
    write_markdown_front_matter,
)


class TestFrontMatterText:
    def test_missing_permissive_preserves_original_text(self) -> None:
        text = "Body\r\nwithout header\r\n"
        assert split_front_matter_text(text, missing="empty") == ({}, text)

    def test_missing_strict_raises(self) -> None:
        with pytest.raises(FrontMatterError, match="must start"):
            split_front_matter_text("Body")

    def test_timestamps_can_remain_strings(self) -> None:
        metadata, _ = split_front_matter_text(
            "---\ndate: 2026-06-13\nat: 2026-06-13T10:00:00Z\n---\n",
            preserve_yaml_timestamps_as_strings=True,
        )
        assert metadata == {
            "date": "2026-06-13",
            "at": "2026-06-13T10:00:00Z",
        }

    def test_timestamp_option_does_not_change_default_loader(self) -> None:
        split_front_matter_text(
            "---\ndate: 2026-06-13\n---\n",
            preserve_yaml_timestamps_as_strings=True,
        )
        metadata, _ = split_front_matter_text("---\ndate: 2026-06-13\n---\n")
        assert metadata["date"] == date(2026, 6, 13)

    def test_template_placeholder_can_be_quoted(self) -> None:
        metadata, _ = split_front_matter_text(
            "---\ntitle: {{title}}\n---\n",
            quote_template_placeholders=True,
        )
        assert metadata == {"title": "{{title}}"}

    def test_template_placeholders_anywhere_mixed_scalar(self) -> None:
        metadata, _ = split_front_matter_text(
            "---\nCreated: created {{date}}\n---\n",
            quote_template_placeholders="anywhere",
        )
        assert metadata == {"Created": "created {{date}}"}

    def test_template_placeholders_anywhere_already_quoted(self) -> None:
        metadata, _ = split_front_matter_text(
            '---\nTitle: "{{title}}"\n---\n',
            quote_template_placeholders="anywhere",
        )
        assert metadata == {"Title": "{{title}}"}

    def test_key_order_and_block_list(self) -> None:
        rendered = render_front_matter_text(
            {"title": "Example", "id": "x", "tags": ["a", "b"]},
            key_order=("id", "title"),
        )
        assert rendered.index("id: x") < rendered.index("title: Example")
        assert "tags:\n- a\n- b\n" in rendered

    def test_minimal_style_options(self) -> None:
        rendered = render_front_matter_text(
            {"title": "Foo", "tags": ["one", "two"], "empty": "", "flag": True},
            "# Body\n",
            key_order=("title", "tags"),
            remaining_key_order="sorted",
            scalar_style="minimal",
            sequence_indent="  ",
            empty_string_style="double",
        )
        assert "tags:\n  - one\n  - two\n" in rendered
        assert 'empty: ""\n' in rendered
        assert "flag: true\n" in rendered
        assert rendered.endswith("---\n# Body\n")

    def test_render_options_override_direct_keywords(self) -> None:
        rendered = render_front_matter_text(
            {"z": 1, "title": "Foo", "a": 2},
            scalar_style="pyyaml",
            render_options=FrontMatterRenderOptions(
                key_order=("title",),
                remaining_key_order="sorted",
                scalar_style="minimal",
            ),
        )
        assert rendered.splitlines()[1:4] == ["title: Foo", "a: 2", "z: 1"]

    def test_minimal_style_rejects_nested_mapping(self) -> None:
        with pytest.raises(FrontMatterError, match="nested"):
            render_front_matter_text({"x": {"nested": True}}, scalar_style="minimal")

    @pytest.mark.parametrize("key", ["bad: key", "-item", "line\nbreak"])
    def test_minimal_style_rejects_unsafe_keys(self, key: str) -> None:
        with pytest.raises(FrontMatterError, match="safe metadata key"):
            render_front_matter_text({key: "value"}, scalar_style="minimal")

    def test_update_passes_minimal_render_options(self) -> None:
        updated = update_front_matter_text(
            "---\ntitle: Old\n---\n\n# Body\n",
            {"tags": ["one", "two"], "empty": ""},
            key_order=("title", "tags", "empty"),
            body_mode="strip-leading-blank",
            scalar_style="minimal",
            sequence_indent="  ",
            empty_string_style="double",
        )
        assert "tags:\n  - one\n  - two\n" in updated
        assert 'empty: ""\n' in updated
        assert updated.endswith("---\n# Body\n")

    @pytest.mark.parametrize(
        "value",
        ["a: b", "a # b", "[value]", " padded ", "true", "null"],
    )
    def test_ambiguous_strings_are_quoted(self, value: str) -> None:
        rendered = render_front_matter_text({"value": value})
        metadata, _ = split_front_matter_text(rendered)
        assert metadata["value"] == value

    def test_native_scalars_are_unquoted(self) -> None:
        rendered = render_front_matter_text({"enabled": True, "count": 2})
        assert "enabled: true" in rendered
        assert "count: 2" in rendered

    @pytest.mark.parametrize(
        "value",
        [
            "- item",
            "? key",
            "*alias",
            "&anchor",
            "!tag",
            "> folded",
            "| literal",
            "@bad",
            "`bad",
            "%YAML",
            "~",
            "2026-06-13",
        ],
    )
    def test_minimal_style_quotes_yaml_plain_scalar_hazards(self, value: str) -> None:
        rendered = render_front_matter_text({"value": value}, scalar_style="minimal")
        metadata, _ = split_front_matter_text(
            rendered, preserve_yaml_timestamps_as_strings=True
        )
        assert metadata["value"] == value

    @pytest.mark.parametrize(
        "value",
        [
            "- item",
            "? key",
            "*alias",
            "&anchor",
            "!tag",
            "> folded",
            "| literal",
            "@bad",
            "`bad",
            "%YAML",
            "~",
            "2026-06-13",
        ],
    )
    def test_minimal_quotes_yaml_hazards_in_sequence_items(self, value: str) -> None:
        rendered = render_front_matter_text({"items": [value]}, scalar_style="minimal")
        metadata, _ = split_front_matter_text(
            rendered, preserve_yaml_timestamps_as_strings=True
        )
        assert metadata["items"] == [value]

    def test_body_modes(self) -> None:
        assert render_front_matter_text(
            {}, "\nbody\n", body_mode="strip-leading-blank"
        ).endswith("---\nbody\n")
        assert render_front_matter_text(
            {}, "body\n\n", body_mode="ensure-single-final-newline"
        ).endswith("body\n")

    def test_update_missing_document(self) -> None:
        rendered = update_front_matter_text("Body\n", {"status": "new"})
        assert split_front_matter_text(rendered) == (
            {"status": "new"},
            "Body\n",
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
