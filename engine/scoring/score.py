"""Public health score (primary) and ripple score (secondary). SDD section 7.

Weights live in the theme file under "scoring".
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from engine.core.pipeline import RunResult
from engine.scoring.diff import Diff


@dataclass(frozen=True)
class HealthScore:
    """Weighted sum of four parts, each capped at plus or minus its weight."""

    deaths_part: float
    cases_part: float
    coverage_part: float
    equity_part: float
    total: float

    def to_dict(self) -> dict[str, float]:
        """Plain-dict form."""
        return asdict(self)


@dataclass(frozen=True)
class RippleScore:
    """reach x depth x surprise."""

    reach: int  # places plus domains touched by events only the player's run has
    depth: int  # longest cause chain from an action to such an event
    surprise: float  # 1 - share of noise runs at least as far from typical as this run
    total: float

    def to_dict(self) -> dict[str, float]:
        """Plain-dict form."""
        return asdict(self)


def _capped(value: float, weight: float) -> float:
    return max(-weight, min(weight, value * weight)) + 0.0  # + 0.0 turns -0.0 into 0.0


def public_health_score(result: Diff, weights: Mapping[str, Any]) -> HealthScore:
    """Score relative to baseline: deaths averted, cases averted, coverage, equity."""
    deaths = _capped(result.deaths_averted / max(1, result.baseline.deaths),
                     weights["weight_deaths"])
    cases = _capped(result.cases_averted / max(1, result.baseline.cases), weights["weight_cases"])
    coverage = _capped(result.coverage_gain / weights["coverage_full_marks_gain"],
                       weights["weight_coverage"])
    equity = _capped(result.gap_reduction / weights["equity_full_marks_gain"],
                     weights["weight_equity"])
    total = deaths + cases + coverage + equity
    return HealthScore(round(deaths, 1), round(cases, 1), round(coverage, 1), round(equity, 1),
                       round(total, 1))


def chain_depths(player: RunResult) -> dict[int, int]:
    """For each event that descends from an action: length of its longest chain."""
    depth: dict[int, int] = {}
    for event in player.log:
        if not player.log.is_tainted(event.id):
            continue
        depth[event.id] = 1 + max((depth.get(cause, 0) for cause in event.causes), default=0)
    return depth


def surprise(player_cases: int, noise_cases: Sequence[int]) -> float:
    """How unusual the player's case count is among no-action runs with other dice."""
    if not noise_cases:
        return 0.0
    ordered = sorted(noise_cases)
    typical = ordered[len(ordered) // 2]
    distance = abs(player_cases - typical)
    at_least_as_far = sum(1 for cases in noise_cases if abs(cases - typical) >= distance)
    return round(1.0 - at_least_as_far / len(noise_cases), 3)


def ripple_score(player: RunResult, result: Diff, surprise_value: float) -> RippleScore:
    """Reach, depth and surprise of the player's ripple."""
    depths = chain_depths(player)
    places: set[str] = set()
    domains: set[str] = set()
    depth = 0
    for event_id in result.only_player:
        if event_id in depths:
            event = player.log.get(event_id)
            places.add(event.place_id)
            domains.add(event.domain)
            depth = max(depth, depths[event_id])
    reach = len(places) + len(domains)
    return RippleScore(reach, depth, surprise_value, round(reach * depth * surprise_value, 1))
