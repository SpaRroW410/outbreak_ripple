"""Shared fixtures. Content is loaded from the repository's `content/` folder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from engine.content import Content
from tools.experiments import load_content

REPORTS = Path(__file__).resolve().parent.parent / "reports"


@pytest.fixture(scope="session")
def content() -> Content:
    """The real game content."""
    return load_content()


@pytest.fixture(scope="session")
def small_content() -> Content:
    """Same content with a 2-block, 6-village district (fast, brute-forceable)."""
    return load_content(small=True)


def write_report(name: str, data: dict[str, Any]) -> None:
    """Save measured numbers to reports/<name>.json for docs/QUALITY_REPORT.md."""
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / f"{name}.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
