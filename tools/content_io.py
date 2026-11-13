"""Read the JSON files under `content/` into one bundle dict.

Bundle layout:
  version       text from content/VERSION
  parameters    name -> {value, unit, source, status, note}   (all parameter files merged)
  cards         list of action cards                          (all card files merged)
  concepts      list of concept cards
  competencies  list of competency entries
  themes        theme id -> theme
  i18n          language code -> {string id -> text}
  quizzes       list of quiz items
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"


def read_json(path: Path) -> Any:
    """Parse one JSON file."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _merged_lists(folder: Path) -> list[Any]:
    """Concatenate the JSON lists in every file of a folder (sorted by file name)."""
    items: list[Any] = []
    for path in sorted(folder.glob("*.json")):
        items.extend(read_json(path))
    return items


def load_bundle(content_dir: Path = CONTENT_DIR) -> dict[str, Any]:
    """Load everything under `content/` into one dict."""
    parameters: dict[str, Any] = {}
    for path in sorted((content_dir / "parameters").glob("*.json")):
        for name, entry in read_json(path).items():
            if name in parameters:
                raise ValueError(f"parameter {name} defined twice")
            parameters[name] = entry
    themes = {path.stem: read_json(path)
              for path in sorted((content_dir / "themes").glob("*.json"))}
    i18n = {path.stem: read_json(path)
            for path in sorted((content_dir / "i18n").glob("*.json"))}
    return {
        "version": (content_dir / "VERSION").read_text(encoding="utf-8").strip(),
        "parameters": parameters,
        "cards": _merged_lists(content_dir / "cards"),
        "concepts": _merged_lists(content_dir / "concepts"),
        "competencies": read_json(content_dir / "competencies.json"),
        "themes": themes,
        "i18n": i18n,
        "quizzes": _merged_lists(content_dir / "quizzes"),
    }
