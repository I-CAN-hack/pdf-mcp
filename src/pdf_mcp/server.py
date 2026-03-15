"""PDF MCP Server - Read, render, and search PDF files via MCP."""

import tempfile
from typing import Literal

import fitz  # PyMuPDF
import pymupdf4llm
from mcp.server.fastmcp import FastMCP, Image

mcp = FastMCP(
    "pdf-mcp",
    instructions="MCP server for reading and searching PDF files",
)

HEADER_FOOTER_MARGIN_PTS = 50


@mcp.tool()
def get_pdf_info(filename: str) -> dict:
    """Get metadata and basic info about a PDF file.

    Returns page count, title, author, subject, creator, producer,
    creation/modification dates, and encryption info.
    """
    doc = fitz.open(filename)
    info = {
        "filename": filename,
        "page_count": doc.page_count,
        "metadata": doc.metadata,
        "is_encrypted": doc.is_encrypted,
    }
    doc.close()
    return info


@mcp.tool()
def get_table_of_contents(filename: str) -> list[dict]:
    """Get the table of contents (bookmarks/outline) from a PDF.

    Returns a list of entries with level, title, and page number.
    These correspond to the sections shown in a PDF reader's sidebar.
    """
    doc = fitz.open(filename)
    toc = doc.get_toc()
    doc.close()
    return [{"level": level, "title": title, "page": page} for level, title, page in toc]


@mcp.tool()
def get_page_text(
    filename: str,
    start_page: int = 1,
    end_page: int | None = None,
    format: Literal["json", "text", "markdown", "html"] = "json",
    include_headers_footers: bool = True,
) -> str | list[dict]:
    """Extract text content from one or more PDF pages.

    Args:
        filename: Path to the PDF file.
        start_page: First page number (1-indexed, inclusive).
        end_page: Last page number (1-indexed, inclusive). Defaults to start_page.
        format: Output format. "json" returns structured page data with block/line/span
                detail. "text" returns plain text. "markdown" returns markdown via
                PyMuPDF4LLM. "html" returns HTML.
        include_headers_footers: If False, crops top/bottom margins to exclude
                                 headers and footers. Default True.
    """
    doc = fitz.open(filename)

    if end_page is None:
        end_page = start_page

    # 0-indexed page list
    pages = list(range(start_page - 1, end_page))

    if format == "markdown":
        if not include_headers_footers:
            for page_idx in pages:
                page = doc[page_idx]
                r = page.rect
                page.set_cropbox(
                    fitz.Rect(
                        r.x0,
                        r.y0 + HEADER_FOOTER_MARGIN_PTS,
                        r.x1,
                        r.y1 - HEADER_FOOTER_MARGIN_PTS,
                    )
                )
        result = pymupdf4llm.to_markdown(doc, pages=pages, show_progress=False)
        doc.close()
        return result

    results = []
    for page_idx in pages:
        page = doc[page_idx]
        clip = None
        if not include_headers_footers:
            r = page.rect
            clip = fitz.Rect(
                r.x0,
                r.y0 + HEADER_FOOTER_MARGIN_PTS,
                r.x1,
                r.y1 - HEADER_FOOTER_MARGIN_PTS,
            )

        if format == "text":
            results.append(page.get_text("text", clip=clip))
        elif format == "html":
            results.append(page.get_text("html", clip=clip))
        else:  # json
            data = page.get_text("dict", clip=clip)
            data["page_number"] = page_idx + 1
            results.append(data)

    doc.close()

    if format == "text":
        return "\n\n--- Page Break ---\n\n".join(results)
    if format == "html":
        return "\n".join(results)
    return results  # json: list of dicts


@mcp.tool()
def get_page_image(
    filename: str,
    page: int = 1,
    dpi: int = 150,
    output: Literal["base64", "file"] = "base64",
):
    """Render a single PDF page as a PNG image.

    Args:
        filename: Path to the PDF file.
        page: Page number (1-indexed).
        dpi: Image resolution. Default 150 (good balance of readability and size).
        output: "base64" returns the image inline as MCP image content.
                "file" writes to a temp file and returns the path.
    """
    doc = fitz.open(filename)
    pdf_page = doc[page - 1]
    pixmap = pdf_page.get_pixmap(dpi=dpi)
    png_bytes = pixmap.tobytes("png")
    doc.close()

    if output == "file":
        tmp = tempfile.NamedTemporaryFile(
            suffix=".png", delete=False, prefix="pdf_page_"
        )
        tmp.write(png_bytes)
        tmp.close()
        return f"Image saved to {tmp.name} ({pixmap.width}x{pixmap.height}px)"

    return Image(data=png_bytes, format="png")


@mcp.tool()
def search_text(
    filename: str,
    query: str,
    context_chars: int = 100,
) -> list[dict]:
    """Search for text in a PDF file (case-insensitive).

    Returns a list of hits with page number and surrounding context.

    Args:
        filename: Path to the PDF file.
        query: Text to search for.
        context_chars: Characters of context to include around each hit. Default 100.
    """
    doc = fitz.open(filename)
    query_lower = query.lower()
    hits = []

    for page_idx in range(doc.page_count):
        text = doc[page_idx].get_text("text")
        text_lower = text.lower()
        pos = 0

        while True:
            idx = text_lower.find(query_lower, pos)
            if idx == -1:
                break
            ctx_start = max(0, idx - context_chars)
            ctx_end = min(len(text), idx + len(query) + context_chars)
            hits.append({
                "page": page_idx + 1,
                "context": text[ctx_start:ctx_end],
            })
            pos = idx + 1

    doc.close()
    return hits


def main():
    mcp.run()


if __name__ == "__main__":
    main()
