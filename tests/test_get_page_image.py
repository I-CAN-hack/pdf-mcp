import os
from pathlib import Path

from mcp.server.fastmcp import Image


class TestGetPageImageBase64:
    def test_returns_image_object(self, basic_pdf, call_tool):
        result = call_tool("get_page_image", filename=basic_pdf, page=1)
        assert isinstance(result, Image)

    def test_image_has_data(self, basic_pdf, call_tool):
        result = call_tool("get_page_image", filename=basic_pdf, page=1)
        assert len(result.data) > 0

    def test_png_signature(self, basic_pdf, call_tool):
        result = call_tool("get_page_image", filename=basic_pdf, page=1)
        assert result.data[:4] == b"\x89PNG"

    def test_different_pages(self, basic_pdf, call_tool):
        img1 = call_tool("get_page_image", filename=basic_pdf, page=1)
        img2 = call_tool("get_page_image", filename=basic_pdf, page=2)
        assert img1.data != img2.data


class TestGetPageImageFile:
    def test_returns_string_with_path(self, basic_pdf, call_tool):
        result = call_tool("get_page_image", filename=basic_pdf, page=1, output="file")
        assert isinstance(result, str)
        assert "Image saved to" in result

    def test_file_exists(self, basic_pdf, call_tool):
        result = call_tool("get_page_image", filename=basic_pdf, page=1, output="file")
        path = result.split("Image saved to ")[1].split(" (")[0]
        assert Path(path).exists()
        os.unlink(path)

    def test_file_is_valid_png(self, basic_pdf, call_tool):
        result = call_tool("get_page_image", filename=basic_pdf, page=1, output="file")
        path = result.split("Image saved to ")[1].split(" (")[0]
        with open(path, "rb") as f:
            assert f.read(4) == b"\x89PNG"
        os.unlink(path)

    def test_file_includes_dimensions(self, basic_pdf, call_tool):
        result = call_tool("get_page_image", filename=basic_pdf, page=1, output="file")
        assert "px)" in result


class TestGetPageImageDpi:
    def test_higher_dpi_larger_file(self, basic_pdf, call_tool):
        low = call_tool("get_page_image", filename=basic_pdf, page=1, dpi=72)
        high = call_tool("get_page_image", filename=basic_pdf, page=1, dpi=300)
        assert len(high.data) > len(low.data)

    def test_default_dpi(self, basic_pdf, call_tool):
        default = call_tool("get_page_image", filename=basic_pdf, page=1)
        explicit_150 = call_tool("get_page_image", filename=basic_pdf, page=1, dpi=150)
        assert len(default.data) == len(explicit_150.data)


class TestGetPageImageDiagrams:
    def test_diagrams_renders(self, diagrams_pdf, call_tool):
        result = call_tool("get_page_image", filename=diagrams_pdf, page=1)
        assert isinstance(result, Image)
        assert len(result.data) > 0

    def test_diagrams_file_output(self, diagrams_pdf, call_tool):
        result = call_tool("get_page_image", filename=diagrams_pdf, page=1, output="file")
        path = result.split("Image saved to ")[1].split(" (")[0]
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0
        os.unlink(path)
