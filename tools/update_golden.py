"""Golden run (SDD 10.8): a fixed seed and fixed plays give a stored event-log hash.

`python -m tools.update_golden` rewrites tests/golden/golden.json. Do this only
for an intentional behaviour change, and say so in NEWS.md.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.runner import Play, run
from tools.experiments import load_content

GOLDEN_FILE = Path(__file__).resolve().parent.parent / "tests" / "golden" / "golden.json"
SEED = "golden-1"
PLAYS = [Play(0, "press_note", "D"), Play(1, "mop_up_campaign", "B01"),
         Play(2, "contact_tracing", "B01V01"), Play(3, "redirect_stock", "B02"),
         Play(4, "community_meeting", "B02V02"), Play(5, "school_closure", "B01V02")]


def compute() -> dict[str, Any]:
    """Run the golden scenario and summarise it."""
    result = run(load_content(), SEED, PLAYS)
    return {"seed": SEED,
            "plays": [[play.turn, play.card_id, play.target] for play in PLAYS],
            "events": len(result.log), "digest": result.log.digest()}


if __name__ == "__main__":
    GOLDEN_FILE.write_text(json.dumps(compute(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {GOLDEN_FILE}")
