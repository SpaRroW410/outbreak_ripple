"""Outcome metrics of one run, read from its final state and event log.

This layer sits above the domains, so it may name their state keys.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from engine.core.pipeline import RunResult


@dataclass(frozen=True)
class Outcome:
    """Headline numbers of a run."""

    cases: int  # true cases (the player only ever saw reported cases)
    reported_cases: int
    deaths: int
    coverage: float  # share of the district population vaccinated
    coverage_gap: float  # mean coverage of best third of villages minus worst third
    mean_trust: float
    outbreaks: int  # villages where an outbreak was declared
    stockouts: int
    sessions_missed: int

    def to_dict(self) -> dict[str, float]:
        """Plain-dict form."""
        return asdict(self)


def _total(result: RunResult, key: str) -> float:
    return float(sum(float(value) for value in result.final_state.get(key, {}).values()))


def village_coverage(result: RunResult) -> dict[str, float]:
    """Vaccinated share per village at the end of the run."""
    vaccinated = result.final_state.get("infectious.vaccinated", {})
    return {village.id: float(vaccinated.get(village.id, 0)) / village.population
            for village in result.district.villages}


def outcome(result: RunResult) -> Outcome:
    """Compute the headline numbers."""
    coverage = sorted(village_coverage(result).values())
    third = max(1, len(coverage) // 3)
    gap = sum(coverage[-third:]) / third - sum(coverage[:third]) / third
    trust = result.final_state.get("systems.trust", {})
    kinds = [event.kind for event in result.log]
    return Outcome(
        cases=int(_total(result, "infectious.cum_cases")),
        reported_cases=int(_total(result, "infectious.reported_cases")),
        deaths=int(_total(result, "infectious.D")),
        coverage=_total(result, "infectious.vaccinated") / result.district.population,
        coverage_gap=gap,
        mean_trust=_total(result, "systems.trust") / max(1, len(trust)),
        outbreaks=kinds.count("infectious.outbreak_declared"),
        stockouts=kinds.count("systems.stockout"),
        sessions_missed=kinds.count("systems.session_missed"),
    )
