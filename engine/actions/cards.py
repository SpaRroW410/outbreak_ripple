"""Action card data type and parser. Cards are JSON in `content/cards/`."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

FAMILIES = ("surveillance", "immunisation", "communication", "staffing", "investigation",
            "meddle")
TARGET_KINDS = ("village", "block", "district")


@dataclass(frozen=True)
class Card:
    """One action card (SDD section 6)."""

    id: str
    name: str
    family: str
    description: str
    budget_cost: int
    action_points: int
    target_kind: str  # "village", "block" or "district"
    effects: tuple[Mapping[str, Any], ...]
    concepts: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Plain-dict form for the UI."""
        return {"id": self.id, "name": self.name, "family": self.family,
                "description": self.description, "budget_cost": self.budget_cost,
                "action_points": self.action_points, "target_kind": self.target_kind,
                "concepts": list(self.concepts)}


def parse_card(raw: Mapping[str, Any]) -> Card:
    """Build a Card from its JSON form (validated by tools/validate_content.py)."""
    return Card(
        id=raw["id"], name=raw["name"], family=raw["family"], description=raw["description"],
        budget_cost=int(raw["cost"]["budget"]), action_points=int(raw["cost"]["action_points"]),
        target_kind=raw["targets"], effects=tuple(raw["effects"]),
        concepts=tuple(raw["concepts"]))
