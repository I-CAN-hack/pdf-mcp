class TestGetTableOfContents:
    def test_basic_toc(self, basic_pdf, call_tool):
        result = call_tool("get_table_of_contents", filename=basic_pdf)
        assert result["total_entries"] == 3
        entries = result["entries"]
        assert entries[0] == {"level": 1, "title": "Chapter 1", "page": 1}
        assert entries[1] == {"level": 1, "title": "Chapter 2", "page": 2}
        assert entries[2] == {"level": 1, "title": "Chapter 3", "page": 3}

    def test_nested_toc_entries(self, nested_toc_pdf, call_tool):
        result = call_tool("get_table_of_contents", filename=nested_toc_pdf)
        assert result["total_entries"] == 9

    def test_nested_toc_levels(self, nested_toc_pdf, call_tool):
        result = call_tool("get_table_of_contents", filename=nested_toc_pdf)
        levels = [e["level"] for e in result["entries"]]
        assert levels == [1, 1, 2, 2, 3, 3, 1, 2, 2]

    def test_nested_toc_titles(self, nested_toc_pdf, call_tool):
        result = call_tool("get_table_of_contents", filename=nested_toc_pdf)
        titles = [e["title"] for e in result["entries"]]
        assert "Introduction" in titles
        assert "Database Layer" in titles
        assert "Kubernetes" in titles

    def test_nested_toc_page_numbers(self, nested_toc_pdf, call_tool):
        result = call_tool("get_table_of_contents", filename=nested_toc_pdf)
        pages = [e["page"] for e in result["entries"]]
        assert pages == list(range(1, 10))

    def test_no_toc(self, search_pdf, call_tool):
        result = call_tool("get_table_of_contents", filename=search_pdf)
        assert result["total_entries"] == 0
        assert result["entries"] == []

    def test_no_toc_diagrams(self, diagrams_pdf, call_tool):
        result = call_tool("get_table_of_contents", filename=diagrams_pdf)
        assert result["total_entries"] == 0
        assert result["entries"] == []

    def test_no_auto_trim_small_toc(self, nested_toc_pdf, call_tool):
        result = call_tool("get_table_of_contents", filename=nested_toc_pdf)
        assert "auto_trimmed_to_level" not in result
        assert "hint" not in result


class TestAutoTrim:
    """Test auto-trimming with 402-entry, 4-level deep mega TOC.

    mega_toc.pdf structure:
      2 volumes (L1) × 8 chapters (L2) × 8 sections (L3) × 2 subsections (L4)

      Cumulative:  ≤L1=2,  ≤L2=18,  ≤L3=146,  ≤L4=402
      Threshold: 100
    """

    def test_full_toc_auto_trims_to_level_2(self, mega_toc_pdf, call_tool):
        """Full TOC (402 entries) auto-trims to level 2 (18 entries ≤ 100)."""
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf)
        assert result["auto_trimmed_to_level"] == 2
        assert result["total_entries"] == 18
        assert all(e["level"] <= 2 for e in result["entries"])

    def test_auto_trim_hint_present(self, mega_toc_pdf, call_tool):
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf)
        assert "hint" in result
        assert "402" in result["hint"]
        assert "18" in result["hint"]
        assert "level 2" in result["hint"]

    def test_auto_trim_entries_are_volumes_and_chapters(self, mega_toc_pdf, call_tool):
        """Trimmed entries should be exactly the 2 volumes + 16 chapters."""
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf)
        entries = result["entries"]
        assert len(entries) == 18
        volumes = [e for e in entries if e["level"] == 1]
        chapters = [e for e in entries if e["level"] == 2]
        assert len(volumes) == 2
        assert len(chapters) == 16

    def test_explicit_max_level_skips_auto_trim(self, mega_toc_pdf, call_tool):
        """When max_level is explicitly set, auto-trim must not activate."""
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf, max_level=4)
        assert "auto_trimmed_to_level" not in result
        assert "hint" not in result
        assert result["total_entries"] == 402

    def test_explicit_max_level_3(self, mega_toc_pdf, call_tool):
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf, max_level=3)
        assert "auto_trimmed_to_level" not in result
        assert result["total_entries"] == 146

    def test_explicit_max_level_1(self, mega_toc_pdf, call_tool):
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf, max_level=1)
        assert result["total_entries"] == 2
        assert all(e["level"] == 1 for e in result["entries"])


class TestAutoTrimWithParent:
    """Test auto-trim when filtering by parent.

    Volume 1 subtree: 8 ch + 64 sec + 128 subsec = 200 children
      ≤L2=8, ≤L3=72, ≤L4=200  → auto-trim to L3 (72 entries)
      applied_max_level = 3 - 1 = 2 (relative to Volume 1)

    Chapter 1.1 subtree: 8 sec + 16 subsec = 24 children (< 100, no trim)
    """

    def test_parent_subtree_auto_trims(self, mega_toc_pdf, call_tool):
        """Volume 1's 200-entry subtree should auto-trim to 72 entries."""
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf, parent="Volume 1")
        assert result["auto_trimmed_to_level"] == 2  # relative to parent
        assert result["total_entries"] == 72
        assert "hint" in result

    def test_parent_subtree_trimmed_levels(self, mega_toc_pdf, call_tool):
        """After trimming, only chapters (L2) and sections (L3) remain."""
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf, parent="Volume 1")
        levels = {e["level"] for e in result["entries"]}
        assert levels == {2, 3}

    def test_parent_small_subtree_no_trim(self, mega_toc_pdf, call_tool):
        """Chapter 1.1 subtree (24 entries) should not trigger auto-trim."""
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf, parent="Chapter 1.1")
        assert "auto_trimmed_to_level" not in result
        assert "hint" not in result
        assert result["total_entries"] == 24

    def test_parent_small_subtree_all_levels(self, mega_toc_pdf, call_tool):
        """Small subtree should include all levels (sections + subsections)."""
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf, parent="Chapter 1.1")
        levels = {e["level"] for e in result["entries"]}
        assert levels == {3, 4}

    def test_parent_with_explicit_max_level_1(self, mega_toc_pdf, call_tool):
        """parent + max_level=1 → direct children only, no auto-trim."""
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf, parent="Volume 1", max_level=1)
        assert "auto_trimmed_to_level" not in result
        assert result["total_entries"] == 8
        assert all(e["level"] == 2 for e in result["entries"])

    def test_parent_with_explicit_max_level_2(self, mega_toc_pdf, call_tool):
        """parent + max_level=2 → children + grandchildren, no auto-trim."""
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf, parent="Volume 1", max_level=2)
        assert "auto_trimmed_to_level" not in result
        assert result["total_entries"] == 72

    def test_parent_not_found(self, mega_toc_pdf, call_tool):
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf, parent="Nonexistent Section")
        assert result["error"] == "No TOC entry matching 'Nonexistent Section'"
        assert result["total_entries"] == 0

    def test_parent_case_insensitive(self, mega_toc_pdf, call_tool):
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf, parent="volume 1")
        assert result["total_entries"] > 0

    def test_parent_partial_match(self, mega_toc_pdf, call_tool):
        """Parent matching is substring-based."""
        result = call_tool("get_table_of_contents", filename=mega_toc_pdf, parent="Chapter 2.")
        assert result["total_entries"] > 0


class TestAutoTrimOldPdf:
    """Regression tests with large_toc.pdf (205 entries, 3 levels)."""

    def test_auto_trim_large_toc(self, large_toc_pdf, call_tool):
        """large_toc.pdf: 205 entries, auto-trims to level 2 (45 entries)."""
        result = call_tool("get_table_of_contents", filename=large_toc_pdf)
        assert result["auto_trimmed_to_level"] == 2
        assert result["total_entries"] == 45
        assert "hint" in result
        assert all(e["level"] <= 2 for e in result["entries"])

    def test_no_auto_trim_when_explicit_max_level(self, large_toc_pdf, call_tool):
        result = call_tool("get_table_of_contents", filename=large_toc_pdf, max_level=3)
        assert "auto_trimmed_to_level" not in result
        assert "hint" not in result
