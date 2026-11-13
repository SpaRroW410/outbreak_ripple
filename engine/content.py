"""Typed access to the content bundle (the JSON files under `content/`).

The engine does no file I/O. Callers (tests, tools, the web worker) read the
JSON files into one dict, the "bundle", and pass it in. The bundle layout is
produced by `tools/content_io.py` and described in docs/CONTENT_GUIDE.md.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from engine.actions.cards import Card, parse_card


@dataclass(frozen=True)
class Content:
    """Parsed content: parameters, theme, cards and concept cards."""

    version: str
    params: dict[str, float]
    parameter_status: dict[str, str]
    theme: Mapping[str, Any]
    cards: dict[str, Card]
    concepts: dict[str, Mapping[str, Any]]
    competencies: dict[str, Mapping[str, Any]]


def parse_content(bundle: Mapping[str, Any], theme_id: str = "default") -> Content:
    """Build a `Content` from a bundle dict."""
    parameters = bundle["parameters"]
    cards = [parse_card(raw) for raw in bundle["cards"]]
    return Content(
        version=str(bundle["version"]),
        params={name: float(entry["value"]) for name, entry in sorted(parameters.items())},
        parameter_status={name: str(entry["status"]) for name, entry in parameters.items()},
        theme=bundle["themes"][theme_id],
        cards={card.id: card for card in sorted(cards, key=lambda card: card.id)},
        concepts={concept["id"]: concept for concept in bundle["concepts"]},
        competencies={entry["id"]: entry for entry in bundle["competencies"]},
    )
