# pdf-mcp

An MCP server for reading, rendering, and searching PDF files, built on the **\*nix Agent philosophy**.

This server represents the "everything is a text stream" design decision of Unix, adapted for the "everything is tokens" nature of LLMs. Instead of a catalog of independent tools, it provides a unified interface for composing powerful workflows.

## The *nix Agent Philosophy

- **Unified Surface**: A single `run` tool instead of 15 specialized schemas.
- **Composition**: Native support for pipes (`|`), conditional execution (`&&`, `||`), and sequencing (`;`).
- **Progressive Discovery**: Use `run("help")` or `run("<command>")` without arguments to discover capabilities on-demand.
- **Heuristic Feedback**: Rich error messages and metadata footers (`[exit:N | Xs]`) guide the LLM's learning loop.

## The `run` Tool

The `run` tool accepts a command string. Available sub-commands:

| Command | Usage |
|---|---|
| `info` | Get metadata about a PDF (page count, etc.). Usage: `info <file.pdf>` |
| `toc` | Get the table of contents. Usage: `toc <file.pdf> [--parent <title>]` |
| `cat` | Extract text. Usage: `cat <file.pdf> [--pages <start-end>] [--format md\|json\|text]` |
| `see` | Render a page as a PNG. Usage: `see <file.pdf> [--page <N>]` |
| `grep` | Search text. Usage: `grep <query> <file.pdf>` or piped: `cat ... \| grep <query>` |

## Examples

### Read and Search
```bash
# Extract text and filter for specific keywords in one call
run("cat datasheet.pdf | grep 'Maximum Ratings'")
```

### Discovery & Learning
```bash
# Forgot parameters? Run command bare to see usage
run("see")
```

### Conditional Workflows
```bash
# Check info first, then read if valid
run("info data.pdf && cat data.pdf --pages 1-2")
```

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

## Development

```bash
# Setup environment
uv venv && source .venv/bin/activate
uv pip install -e .

# Run verification tests
python tests/verify_refactor.py
```
