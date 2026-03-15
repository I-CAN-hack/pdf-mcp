from pdf_mcp.server import get_pdf_info


class TestGetPdfInfo:
    def test_basic_metadata(self, basic_pdf):
        info = get_pdf_info(basic_pdf)
        assert info["page_count"] == 3
        assert info["metadata"]["title"] == "Test Document"
        assert info["metadata"]["author"] == "Test Author"
        assert info["metadata"]["subject"] == "Testing"
        assert info["metadata"]["keywords"] == "test, pdf, mcp"
        assert info["metadata"]["creator"] == "generate.py"
        assert info["is_encrypted"] is False

    def test_filename_returned(self, basic_pdf):
        info = get_pdf_info(basic_pdf)
        assert info["filename"] == basic_pdf

    def test_single_page_pdf(self, diagrams_pdf):
        info = get_pdf_info(diagrams_pdf)
        assert info["page_count"] == 1

    def test_multi_page_pdf(self, nested_toc_pdf):
        info = get_pdf_info(nested_toc_pdf)
        assert info["page_count"] == 9

    def test_search_targets_page_count(self, search_pdf):
        info = get_pdf_info(search_pdf)
        assert info["page_count"] == 3
