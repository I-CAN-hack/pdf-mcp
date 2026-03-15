class TestGetPageTextJson:
    def test_default_format_is_json(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=1)
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], dict)

    def test_json_has_page_number(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=2)
        assert result[0]["page_number"] == 2

    def test_json_has_blocks(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=1)
        assert "blocks" in result[0]
        assert len(result[0]["blocks"]) > 0

    def test_json_page_range(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=1, end_page=3, format="json")
        assert len(result) == 3
        assert result[0]["page_number"] == 1
        assert result[2]["page_number"] == 3


class TestGetPageTextPlain:
    def test_text_format_returns_string(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=1, format="text")
        assert isinstance(result, str)

    def test_text_contains_content(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=1, format="text")
        assert "Chapter 1" in result
        assert "introductory material" in result

    def test_text_page_range_has_breaks(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=1, end_page=2, format="text")
        assert "--- Page Break ---" in result
        assert "Chapter 1" in result
        assert "Chapter 2" in result

    def test_text_single_page_no_break(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=1, format="text")
        assert "--- Page Break ---" not in result


class TestGetPageTextMarkdown:
    def test_markdown_returns_string(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=1, format="markdown")
        assert isinstance(result, str)

    def test_markdown_contains_content(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=1, format="markdown")
        assert "Chapter 1" in result

    def test_markdown_page_range(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=1, end_page=3, format="markdown")
        assert "Chapter 1" in result
        assert "Chapter 3" in result


class TestGetPageTextHtml:
    def test_html_returns_string(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=1, format="html")
        assert isinstance(result, str)

    def test_html_has_tags(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=1, format="html")
        assert "<div" in result
        assert "<span" in result

    def test_html_contains_content(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=1, format="html")
        assert "Chapter 1" in result


class TestGetPageTextHeaderFooter:
    def test_with_headers_footers(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=1, format="text", include_headers_footers=True)
        assert "Header" in result
        assert "Page 1 of 3" in result

    def test_without_headers_footers(self, basic_pdf, call_tool):
        result = call_tool(
            "get_page_text", filename=basic_pdf, start_page=1, format="text", include_headers_footers=False
        )
        assert "Header" not in result
        assert "Page 1 of 3" not in result

    def test_body_preserved_without_headers_footers(self, basic_pdf, call_tool):
        result = call_tool(
            "get_page_text", filename=basic_pdf, start_page=1, format="text", include_headers_footers=False
        )
        assert "Chapter 1" in result
        assert "introductory material" in result

    def test_markdown_without_headers_footers(self, basic_pdf, call_tool):
        result = call_tool(
            "get_page_text", filename=basic_pdf, start_page=1, format="markdown", include_headers_footers=False
        )
        assert "Chapter 1" in result
        assert "Header" not in result


class TestGetPageTextEndPageDefault:
    def test_end_page_defaults_to_start(self, basic_pdf, call_tool):
        result = call_tool("get_page_text", filename=basic_pdf, start_page=2, format="text")
        assert "Chapter 2" in result
        assert "Chapter 1" not in result
        assert "Chapter 3" not in result


class TestGetPageTextDiagrams:
    def test_diagrams_text_extraction(self, diagrams_pdf, call_tool):
        result = call_tool("get_page_text", filename=diagrams_pdf, start_page=1, format="text")
        assert "Component A" in result
        assert "Component B" in result
        assert "Pin Configuration" in result
        assert "GPIO_1" in result
