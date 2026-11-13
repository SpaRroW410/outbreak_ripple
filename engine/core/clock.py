"""Tick clock: 1 tick = 1 week; a run is split into decision turns.

Contract: pure arithmetic, no state. Turn `t` starts at tick
`(t * ticks_per_run) // turns`. Defaults (52 ticks, 6 turns) come from
`content/themes/*.json`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Clock:
    """Run length and turn boundaries."""

    ticks_per_run: int = 52
    turns: int = 6

    def turn_start(self, turn: int) -> int:
        """First tick of the given turn (turn == turns gives the end of run)."""
        return (turn * self.ticks_per_run) // self.turns

    def turn_of(self, tick: int) -> int:
        """Index of the turn that contains `tick`."""
        for turn in range(self.turns - 1, -1, -1):
            if tick >= self.turn_start(turn):
                return turn
        return 0

    def is_turn_start(self, tick: int) -> bool:
        """True when a decision turn begins at `tick`."""
        return any(self.turn_start(turn) == tick for turn in range(self.turns))
