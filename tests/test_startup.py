import subprocess
import sys


def test_server_import_does_not_write_to_stdout():
    result = subprocess.run(
        [sys.executable, "-c", "import pdf_mcp.server"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
