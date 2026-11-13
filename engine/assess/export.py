"""Anonymous session export (SDD section 8 and 12).

Contains no personal data: seed, plays, scores, behaviour counters and the
engine and content versions. The participant code and quiz answers are added
in Phase 3.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

EXPORT_SCHEMA_VERSION = 1


def build_export(engine_version: str, content_version: str, seed_text: str,
                 plays: Sequence[Mapping[str, Any]], card_families: Mapping[str, str],
                 scores: Mapping[str, Any], concepts_viewed: Sequence[str]) -> dict[str, Any]:
    """Assemble the export dict. `plays` are {turn, card_id, target} mappings."""
    families = Counter(card_families[str(play["card_id"])] for play in plays)
    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "engine_version": engine_version,
        "content_version": content_version,
        "seed": seed_text,
        "plays": [dict(play) for play in plays],
        "scores": dict(scores),
        "counters": {
            "cards_by_family": dict(sorted(families.items())),
            "concepts_viewed": sorted(set(concepts_viewed)),
        },
    }
