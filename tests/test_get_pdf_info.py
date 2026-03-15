class TestGetPdfInfo:
    def test_basic_metadata(self, basic_pdf, call_tool):
        info = call_tool("get_pdf_info", filename=basic_pdf)
        assert info["page_count"] == 3
        assert info["metadata"]["title"] == "Test Document"
        assert info["metadata"]["author"] == "Test Author"
        assert info["metadata"]["subject"] == "Testing"
        assert info["metadata"]["keywords"] == "test, pdf, mcp"
        assert info["metadata"]["creator"] == "generate.py"
        assert info["is_encrypted"] is False

    def test_filename_returned(self, basic_pdf, call_tool):
        info = call_tool("get_pdf_info", filename=basic_pdf)
        assert info["filename"] == basic_pdf

    def test_single_page_pdf(self, diagrams_pdf, call_tool):
        info = call_tool("get_pdf_info", filename=diagrams_pdf)
        assert info["page_count"] == 1

    def test_multi_page_pdf(self, nested_toc_pdf, call_tool):
        info = call_tool("get_pdf_info", filename=nested_toc_pdf)
        assert info["page_count"] == 9

    def test_search_targets_page_count(self, search_pdf, call_tool):
        info = call_tool("get_pdf_info", filename=search_pdf)
        assert info["page_count"] == 3
