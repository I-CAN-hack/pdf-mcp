"""Shared fixtures for pdf-mcp tests."""

import asyncio
import subprocess
import sys
from pathlib import Path

import pytest

from pdf_mcp.server import mcp

ASSETS = Path(__file__).parent.parent / "assets"


def pytest_configure(config):
    """Generate test PDFs before the test session if they don't exist."""
    expected = ["basic.pdf", "diagrams.pdf", "nested_toc.pdf", "search_targets.pdf", "large_toc.pdf", "mega_toc.pdf"]
    if not all((ASSETS / f).exists() for f in expected):
        subprocess.check_call(
            [sys.executable, str(ASSETS / "generate.py")],
        )


@pytest.fixture
def call_tool():
    """Call an MCP tool by name, going through the real FastMCP call path."""
    def _call(tool_name: str, **kwargs):
        tools = mcp._tool_manager.list_tools()
        tool = next(t for t in tools if t.name == tool_name)
        return asyncio.run(tool.run(kwargs))
    return _call


@pytest.fixture
def basic_pdf() -> str:
    return str(ASSETS / "basic.pdf")


@pytest.fixture
def diagrams_pdf() -> str:
    return str(ASSETS / "diagrams.pdf")


@pytest.fixture
def nested_toc_pdf() -> str:
    return str(ASSETS / "nested_toc.pdf")


@pytest.fixture
def search_pdf() -> str:
    return str(ASSETS / "search_targets.pdf")


@pytest.fixture
def large_toc_pdf() -> str:
    return str(ASSETS / "large_toc.pdf")


@pytest.fixture
def mega_toc_pdf() -> str:
    return str(ASSETS / "mega_toc.pdf")
