"""PDF MCP Server - Read, render, and search PDF files via *nix-style pipes and chains."""

import tempfile
import time
import os
import shlex
import dataclasses
import json
from typing import Literal, List, Optional, Tuple, Callable, Dict

import fitz  # PyMuPDF
import pymupdf4llm
from mcp.server.fastmcp import FastMCP, Image

# --- Configuration ---
mcp = FastMCP(
    "pdf-mcp",
    instructions="""PDF MCP Server - Progressive Discovery Interface.
    
    This server follows the *nix philosophy: everything is text, and tools are composed via pipes (|) and chains (&&, ||, ;).
    
    To discover available commands, call `run(command="help")`.
    To learn about a specific command, call it without arguments, e.g., `run(command="cat")`.
    
    Common patterns:
    - Get info: info file.pdf
    - Read text: cat file.pdf --pages 1-5
    - Search: cat file.pdf | grep "query"
    - View image: see file.pdf --page 1
    """,
)

HEADER_FOOTER_MARGIN_PTS = 50
TOC_AUTO_TRIM_THRESHOLD = 100
MAX_OUTPUT_CHARS = 50 * 1024  # 50KB truncation threshold
OUTPUT_TMP_DIR = "/tmp/pdf-mcp"

@dataclasses.dataclass
class CommandResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: int = 0
    binary_data: Optional[bytes] = None
    binary_format: Optional[str] = None

# --- Sub-command Handlers ---

def handle_info(args: List[str], stdin: str = "") -> CommandResult:
    """Get metadata and basic info about a PDF file. Usage: info <filename>"""
    if not args:
        return CommandResult(stderr="usage: info <filename>", exit_code=1)
    
    filename = args[0]
    try:
        doc = fitz.open(filename)
        info = {
            "filename": filename,
            "page_count": doc.page_count,
            "metadata": doc.metadata,
            "is_encrypted": doc.is_encrypted,
        }
        doc.close()
        return CommandResult(stdout=json.dumps(info, indent=2))
    except Exception as e:
        return CommandResult(stderr=str(e), exit_code=1)

def handle_toc(args: List[str], stdin: str = "") -> CommandResult:
    """Get the table of contents. Usage: toc <filename> [--parent <title>] [--max-level <N>]"""
    if not args:
        return CommandResult(stderr="usage: toc <filename> [--parent <title>] [--max-level <N>]", exit_code=1)
    
    filename = args[0]
    parent = None
    max_level = None
    
    # Simple arg parsing
    i = 1
    while i < len(args):
        if args[i] == "--parent" and i + 1 < len(args):
            parent = args[i+1]
            i += 2
        elif args[i] == "--max-level" and i + 1 < len(args):
            max_level = int(args[i+1])
            i += 2
        else:
            i += 1

    try:
        doc = fitz.open(filename)
        toc = doc.get_toc()
        doc.close()

        explicit_max_level = max_level is not None
        base_level = 0

        if parent is not None:
            parent_lower = parent.lower()
            parent_idx = None
            parent_level = None
            for i, (level, title, _page) in enumerate(toc):
                if parent_lower in title.lower():
                    parent_idx = i
                    parent_level = level
                    break
            if parent_idx is None:
                return CommandResult(stderr=f"No TOC entry matching '{parent}'", exit_code=1)
            
            children = []
            for level, title, page in toc[parent_idx + 1 :]:
                if level <= parent_level:
                    break
                children.append((level, title, page))
            toc = children
            base_level = parent_level
            if max_level is not None:
                abs_max_level = parent_level + max_level
                toc = [entry for entry in toc if entry[0] <= abs_max_level]
        elif max_level is not None:
            toc = [entry for entry in toc if entry[0] <= max_level]

        untrimmed_total = len(toc)
        applied_max_level = None
        if not explicit_max_level and len(toc) > TOC_AUTO_TRIM_THRESHOLD:
            levels_present = sorted(set(entry[0] for entry in toc))
            best_level = levels_present[0]
            for try_level in levels_present:
                count = sum(1 for entry in toc if entry[0] <= try_level)
                if count <= TOC_AUTO_TRIM_THRESHOLD:
                    best_level = try_level
                else:
                    break
            toc = [entry for entry in toc if entry[0] <= best_level]
            applied_max_level = best_level - base_level

        entries = [{"level": l, "title": t, "page": p} for l, t, p in toc]
        result = {"total_entries": len(entries), "entries": entries}
        if applied_max_level is not None:
            result["auto_trimmed_to_level"] = applied_max_level
            result["hint"] = f"Trimmed from {untrimmed_total} entries to level {applied_max_level}."
            
        return CommandResult(stdout=json.dumps(result, indent=2))
    except Exception as e:
        return CommandResult(stderr=str(e), exit_code=1)

def handle_cat(args: List[str], stdin: str = "") -> CommandResult:
    """Extract text. Usage: cat <filename> [--pages <start-end>] [--format <json|text|md|html>] [--no-headers]"""
    if not args and not stdin:
        return CommandResult(stderr="usage: cat <filename> [--pages <start-end>] [--format <json|text|md|html>]", exit_code=1)
    
    filename = args[0] if args else None
    pages_str = None
    fmt = "text"
    include_headers = True

    i = 1
    while i < len(args):
        if args[i] == "--pages" and i + 1 < len(args):
            pages_str = args[i+1]
            i += 2
        elif args[i] == "--format" and i + 1 < len(args):
            fmt = args[i+1]
            i += 2
        elif args[i] == "--no-headers":
            include_headers = False
            i += 1
        else:
            i += 1

    try:
        doc = fitz.open(filename) if filename else None
        # Handle cases where we might want to pipe text but for PDF MCP, 
        # 'cat' usually needs the file path.
        if not doc:
             return CommandResult(stderr="Error: cat requires a PDF filename", exit_code=1)

        start_page, end_page = 1, doc.page_count
        if pages_str:
            if "-" in pages_str:
                s, e = pages_str.split("-")
                start_page, end_page = int(s), int(e)
            else:
                start_page = end_page = int(pages_str)

        page_indices = list(range(start_page - 1, min(end_page, doc.page_count)))

        if fmt == "markdown" or fmt == "md":
            if not include_headers:
                for idx in page_indices:
                    page = doc[idx]
                    r = page.rect
                    page.set_cropbox(fitz.Rect(r.x0, r.y0 + HEADER_FOOTER_MARGIN_PTS, r.x1, r.y1 - HEADER_FOOTER_MARGIN_PTS))
            res = pymupdf4llm.to_markdown(doc, pages=page_indices, show_progress=False)
            doc.close()
            return CommandResult(stdout=res)

        results = []
        for idx in page_indices:
            page = doc[idx]
            clip = None
            if not include_headers:
                r = page.rect
                clip = fitz.Rect(r.x0, r.y0 + HEADER_FOOTER_MARGIN_PTS, r.x1, r.y1 - HEADER_FOOTER_MARGIN_PTS)
            
            if fmt == "text":
                results.append(page.get_text("text", clip=clip))
            elif fmt == "html":
                results.append(page.get_text("html", clip=clip))
            else:  # json
                data = page.get_text("dict", clip=clip)
                data["page_number"] = idx + 1
                results.append(data)
        doc.close()

        if fmt == "text":
            return CommandResult(stdout="\n\n--- Page Break ---\n\n".join(results))
        if fmt == "html":
            return CommandResult(stdout="\n".join(results))
        return CommandResult(stdout=json.dumps(results, indent=2))
    except Exception as e:
        return CommandResult(stderr=str(e), exit_code=1)

def handle_see(args: List[str], stdin: str = "") -> CommandResult:
    """Render a page as image. Usage: see <filename> [--page <N>] [--dpi <150>] [--output <base64|file>]"""
    if not args:
        return CommandResult(stderr="usage: see <filename> [--page <N>] [--dpi <150>] [--output <base64|file>]", exit_code=1)
    
    filename = args[0]
    page_num = 1
    dpi = 150
    output_mode = "base64"

    i = 1
    while i < len(args):
        if args[i] == "--page" and i + 1 < len(args):
            page_num = int(args[i+1])
            i += 2
        elif args[i] == "--dpi" and i + 1 < len(args):
            dpi = int(args[i+1])
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_mode = args[i+1]
            i += 2
        else:
            i += 1

    try:
        doc = fitz.open(filename)
        page = doc[page_num - 1]
        pix = page.get_pixmap(dpi=dpi)
        img_bytes = pix.tobytes("png")
        doc.close()

        if output_mode == "file":
             os.makedirs(OUTPUT_TMP_DIR, exist_ok=True)
             with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=OUTPUT_TMP_DIR, prefix="page_") as tmp:
                 tmp.write(img_bytes)
                 return CommandResult(stdout=f"Image saved to {tmp.name} ({pix.width}x{pix.height}px)")
        
        return CommandResult(stdout=f"[image: png, {len(img_bytes)} bytes]", binary_data=img_bytes, binary_format="png")
    except Exception as e:
        return CommandResult(stderr=str(e), exit_code=1)

def handle_grep(args: List[str], stdin: str = "") -> CommandResult:
    """Search text. Usage: cat ... | grep <query> or grep <query> <filename>"""
    if not args and not stdin:
         return CommandResult(stderr="usage: grep <query> [filename]", exit_code=1)
    
    query = args[0]
    content = stdin
    filename = args[1] if len(args) > 1 else None

    try:
        if filename:
            doc = fitz.open(filename)
            hits = []
            for i in range(doc.page_count):
                text = doc[i].get_text("text")
                if query.lower() in text.lower():
                    # Simple mock of context extraction
                    idx = text.lower().find(query.lower())
                    hits.append({"page": i+1, "context": text[max(0, idx-50):idx+len(query)+50]})
            doc.close()
            return CommandResult(stdout=json.dumps(hits, indent=2))
        else:
            # Pipe mode
            lines = [l for l in content.splitlines() if query.lower() in l.lower()]
            return CommandResult(stdout="\n".join(lines))
    except Exception as e:
        return CommandResult(stderr=str(e), exit_code=1)

def handle_help(args: List[str], stdin: str = "") -> CommandResult:
    """Show available commands. Usage: help"""
    help_text = "Available commands:\n"
    for name, func in COMMANDS.items():
        doc = func.__doc__.split(".")[0] if func.__doc__ else "No description"
        help_text += f"  {name:<8} - {doc}\n"
    return CommandResult(stdout=help_text)

COMMANDS = {
    "info": handle_info,
    "toc": handle_toc,
    "cat": handle_cat,
    "see": handle_see,
    "grep": handle_grep,
    "help": handle_help,
}

# --- Core Logic ---

class ChainParser:
    def __init__(self, registry: Dict[str, Callable]):
        self.registry = registry

    def run(self, command_line: str) -> str:
        try:
            tokens = shlex.split(command_line)
        except ValueError as e:
            return f"[error] invalid command line: {e}\n[exit:1 | 0ms]"

        segments = []
        current = []
        for token in tokens:
            if token in ["|", "&&", "||", ";"]:
                segments.append((current, token))
                current = []
            else:
                current.append(token)
        segments.append((current, None))

        last_res = CommandResult()
        stdin = ""
        
        for i, (args, operator) in enumerate(segments):
            if not args: continue
            
            if i > 0:
                prev_op = segments[i-1][1]
                if prev_op == "&&" and last_res.exit_code != 0: break
                if prev_op == "||" and last_res.exit_code == 0: break

            cmd = args[0]
            start = time.time()
            if cmd in self.registry:
                last_res = self.registry[cmd](args[1:], stdin=stdin)
            else:
                last_res = CommandResult(stderr=f"unknown command: {cmd}", exit_code=127)
            last_res.duration_ms = int((time.time() - start) * 1000)

            if operator == "|":
                stdin = last_res.stdout
            else:
                stdin = ""

        return self.present(last_res)

    def present(self, result: CommandResult) -> str | Image:
        # Binary Guard / Direct Image return
        if result.binary_data and result.binary_format == "png":
            return Image(data=result.binary_data, format="png")
        
        output = result.stdout
        if result.exit_code != 0:
            if output: output += "\n"
            output += f"[stderr] {result.stderr}" if result.stderr else "[error] failed"

        # Truncation
        if len(output) > MAX_OUTPUT_CHARS:
            os.makedirs(OUTPUT_TMP_DIR, exist_ok=True)
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, dir=OUTPUT_TMP_DIR, prefix="cmd_") as tmp:
                tmp.write(output.encode("utf-8"))
            output = output[:MAX_OUTPUT_CHARS] + f"\n\n--- output truncated ---\nFull output: {tmp.name}\nExplore: cat {tmp.name} | grep ..."

        return f"{output}\n[exit:{result.exit_code} | {result.duration_ms}ms]"

# --- MCP Tool ---

mcp_parser = ChainParser(COMMANDS)

@mcp.tool()
def run(command: str):
    """Execute a PDF tool or a pipeline of commands.
    
    Available commands:
      info <file.pdf>              - Metadata & page count
      toc <file.pdf>               - Table of contents
      cat <file.pdf> [options]     - Extract text (--pages, --format, --no-headers)
      see <file.pdf> [options]     - Render page (--page, --dpi)
      grep <query> [file.pdf]      - Search text (can be piped)
      
    Operators: | (pipe), && (on success), || (on fail), ; (sequence)
    """
    return mcp_parser.run(command)

def main():
    mcp.run()

if __name__ == "__main__":
    main()
