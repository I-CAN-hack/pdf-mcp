from pdf_mcp.server import get_table_of_contents


class TestGetTableOfContents:
    def test_basic_toc(self, basic_pdf):
        toc = get_table_of_contents(basic_pdf)
        assert len(toc) == 3
        assert toc[0] == {"level": 1, "title": "Chapter 1", "page": 1}
        assert toc[1] == {"level": 1, "title": "Chapter 2", "page": 2}
        assert toc[2] == {"level": 1, "title": "Chapter 3", "page": 3}

    def test_nested_toc_entries(self, nested_toc_pdf):
        toc = get_table_of_contents(nested_toc_pdf)
        assert len(toc) == 9

    def test_nested_toc_levels(self, nested_toc_pdf):
        toc = get_table_of_contents(nested_toc_pdf)
        levels = [e["level"] for e in toc]
        assert levels == [1, 1, 2, 2, 3, 3, 1, 2, 2]

    def test_nested_toc_titles(self, nested_toc_pdf):
        toc = get_table_of_contents(nested_toc_pdf)
        titles = [e["title"] for e in toc]
        assert "Introduction" in titles
        assert "Database Layer" in titles
        assert "Kubernetes" in titles

    def test_nested_toc_page_numbers(self, nested_toc_pdf):
        toc = get_table_of_contents(nested_toc_pdf)
        pages = [e["page"] for e in toc]
        assert pages == list(range(1, 10))

    def test_no_toc(self, search_pdf):
        toc = get_table_of_contents(search_pdf)
        assert toc == []

    def test_no_toc_diagrams(self, diagrams_pdf):
        toc = get_table_of_contents(diagrams_pdf)
        assert toc == []
