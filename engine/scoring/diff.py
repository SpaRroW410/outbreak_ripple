"""Counterfactual diff between the player's run and the no-action baseline (SDD 4.6).

Two events are "the same" when tick, kind and place match. Events that exist
in only one run are the ripple of the player's actions.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from engine.core.events import ACTION_KIND, Event
from engine.core.pipeline import RunResult
from engine.scoring.metrics import Outcome, outcome

Signature = tuple[int, str, str]


@dataclass(frozen=True)
class Diff:
    """What the player changed, relative to the baseline."""

    player: Outcome
    baseline: Outcome
    cases_averted: int
    deaths_averted: int
    coverage_gain: float
    gap_reduction: float
    trust_gain: float
    stockouts_added: int
    only_player: tuple[int, ...]  # ids in the player's log (action events excluded)
    only_baseline: tuple[int, ...]  # ids in the baseline log: events the player prevented

    @property
    def ripple_size(self) -> int:
        """Number of events that exist in exactly one of the two runs."""
        return len(self.only_player) + len(self.only_baseline)

    @property
    def is_zero(self) -> bool:
        """True when the two runs cannot be told apart."""
        return self.ripple_size == 0 and self.player == self.baseline


def signature(event: Event) -> Signature:
    """Identity of an event for comparison across runs."""
    return (event.tick, event.kind, event.place_id)


def _unmatched(events: list[Event], other: list[Event]) -> tuple[int, ...]:
    """Ids of `events` that have no partner with the same signature in `other`."""
    available = Counter(signature(event) for event in other)
    missing: list[int] = []
    for event in events:
        key = signature(event)
        if available[key] > 0:
            available[key] -= 1
        else:
            missing.append(event.id)
    return tuple(missing)


def diff(player: RunResult, baseline: RunResult) -> Diff:
    """Compare a player's run with the baseline run of the same seed."""
    a, b = outcome(player), outcome(baseline)
    player_events = [event for event in player.log if event.kind != ACTION_KIND]
    baseline_events = [event for event in baseline.log if event.kind != ACTION_KIND]
    return Diff(
        player=a, baseline=b,
        cases_averted=b.cases - a.cases,
        deaths_averted=b.deaths - a.deaths,
        coverage_gain=a.coverage - b.coverage,
        gap_reduction=b.coverage_gap - a.coverage_gap,
        trust_gain=a.mean_trust - b.mean_trust,
        stockouts_added=a.stockouts - b.stockouts,
        only_player=_unmatched(player_events, baseline_events),
        only_baseline=_unmatched(baseline_events, player_events),
    )
