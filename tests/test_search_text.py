from pdf_mcp.server import search_text


class TestSearchTextBasic:
    def test_unique_marker_on_two_pages(self, search_pdf):
        hits = search_text(search_pdf, query="UNIQUE_MARKER_ALPHA")
        pages = [h["page"] for h in hits]
        assert pages == [1, 3]

    def test_unique_marker_single_page(self, search_pdf):
        hits = search_text(search_pdf, query="UNIQUE_MARKER_BETA")
        assert len(hits) == 1
        assert hits[0]["page"] == 2

    def test_no_results(self, search_pdf):
        hits = search_text(search_pdf, query="NONEXISTENT_TEXT_XYZ")
        assert hits == []

    def test_multi_page_hits(self, search_pdf):
        hits = search_text(search_pdf, query="resistance")
        pages = [h["page"] for h in hits]
        assert 1 in pages
        assert 2 in pages


class TestSearchTextCaseInsensitive:
    def test_lowercase_query(self, search_pdf):
        hits = search_text(search_pdf, query="unique_marker_alpha")
        assert len(hits) == 2

    def test_mixed_case_query(self, search_pdf):
        hits = search_text(search_pdf, query="Unique_Marker_Alpha")
        assert len(hits) == 2

    def test_case_insensitive_content(self, search_pdf):
        lower = search_text(search_pdf, query="resistance")
        upper = search_text(search_pdf, query="RESISTANCE")
        assert len(lower) == len(upper)


class TestSearchTextContext:
    def test_context_contains_query(self, search_pdf):
        hits = search_text(search_pdf, query="UNIQUE_MARKER_BETA")
        assert "UNIQUE_MARKER_BETA" in hits[0]["context"]

    def test_context_has_surrounding_text(self, search_pdf):
        hits = search_text(search_pdf, query="UNIQUE_MARKER_BETA")
        # The context should include text around the match
        assert len(hits[0]["context"]) > len("UNIQUE_MARKER_BETA")

    def test_custom_context_chars(self, search_pdf):
        short = search_text(search_pdf, query="UNIQUE_MARKER_BETA", context_chars=10)
        long = search_text(search_pdf, query="UNIQUE_MARKER_BETA", context_chars=200)
        assert len(short[0]["context"]) <= len(long[0]["context"])

    def test_zero_context(self, search_pdf):
        hits = search_text(search_pdf, query="UNIQUE_MARKER_BETA", context_chars=0)
        assert hits[0]["context"] == "UNIQUE_MARKER_BETA"


class TestSearchTextHitStructure:
    def test_hit_has_page(self, search_pdf):
        hits = search_text(search_pdf, query="resistance")
        for hit in hits:
            assert "page" in hit
            assert isinstance(hit["page"], int)

    def test_hit_has_context(self, search_pdf):
        hits = search_text(search_pdf, query="resistance")
        for hit in hits:
            assert "context" in hit
            assert isinstance(hit["context"], str)


class TestSearchTextOnOtherPdfs:
    def test_search_basic_pdf(self, basic_pdf):
        hits = search_text(basic_pdf, query="introductory")
        assert len(hits) == 1
        assert hits[0]["page"] == 1

    def test_search_diagrams_pdf(self, diagrams_pdf):
        hits = search_text(diagrams_pdf, query="Component A")
        assert len(hits) == 1
        assert hits[0]["page"] == 1

    def test_search_nested_toc_pdf(self, nested_toc_pdf):
        hits = search_text(nested_toc_pdf, query="Kubernetes")
        assert len(hits) >= 1
