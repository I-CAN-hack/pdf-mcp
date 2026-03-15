"""Shared fixtures for pdf-mcp tests."""

import subprocess
import sys
from pathlib import Path

import pytest

ASSETS = Path(__file__).parent.parent / "assets"


def pytest_configure(config):
    """Generate test PDFs before the test session if they don't exist."""
    expected = ["basic.pdf", "diagrams.pdf", "nested_toc.pdf", "search_targets.pdf"]
    if not all((ASSETS / f).exists() for f in expected):
        subprocess.check_call(
            [sys.executable, str(ASSETS / "generate.py")],
        )


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
