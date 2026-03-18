# pdf-mcp

An MCP server for reading, rendering, and searching PDF files. Built with [PyMuPDF](https://pymupdf.readthedocs.io/) and [PyMuPDF4LLM](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/).

Designed for use with LLMs that need to read datasheets and other PDFs containing diagrams, tables, and technical content.

## Tools

| Tool | Description |
|---|---|
| `get_pdf_info` | Get metadata about a PDF (page count, author, title, etc.) |
| `get_table_of_contents` | Get the outline/bookmarks with page numbers for each section |
| `get_page_text` | Extract text from a page range in `json` (default), `text`, `markdown`, or `html` format. Optionally exclude headers/footers |
| `get_page_image` | Render a single page as a PNG image, returned as base64 or written to a temp file. Configurable DPI (default 150) |
| `search_text` | Case-insensitive text search across the entire PDF, returning page numbers and surrounding context |

All requests are stateless and take the PDF filename as a parameter.

## Setup

Add the following to your `.mcp.json`:

```json
{
  "mcpServers": {
    "pdf-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/I-CAN-hack/pdf-mcp.git", "pdf-mcp"]
    }
  }
}
```

Or for codex run `codex mcp add pdf-mcp -- uvx --from git+https://github.com/I-CAN-hack/pdf-mcp.git pdf-mcp`.

This will automatically install and run the server using `uvx`.

## Development

```bash
# Install dependencies
uv sync

# Generate test PDFs
uv run python assets/generate.py

# Run tests
uv run pytest tests/ -v

# Run the server locally
uv run pdf-mcp
```
