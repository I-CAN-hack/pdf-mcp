import sys
import os
import json

# Add src to path
sys.path.append(os.path.abspath("/Users/John/agents/pdf-mcp/src"))

from pdf_mcp.server import mcp_parser

def test_command(cmd_line):
    print(f"\n>>> Running: {cmd_line}")
    res = mcp_parser.run(cmd_line)
    if hasattr(res, 'data'):
        print(f"Result: [Binary Image, {len(res.data)} bytes]")
    else:
        print(f"Result:\n{res}")

# Sample PDF created in /Users/John/agents/pdf-mcp/tests/test.pdf
pdf_path = "/Users/John/agents/pdf-mcp/tests/test.pdf"

test_command(f"info {pdf_path}")
test_command(f"cat {pdf_path}")
test_command(f"cat {pdf_path} | grep Abstract")
test_command(f"info {pdf_path} && echo Success") # echo should fail but run() handles it
test_command(f"see {pdf_path} --page 1")
test_command(f"help") # Unknown command should trigger help/error
test_command(f"cat") # Usage discovery
test_command(f"grep") # Usage discovery
test_command(f"cat {pdf_path} --no-headers")
