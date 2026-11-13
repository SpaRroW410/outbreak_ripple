"""Model-sanity measurements for the infectious model in a homogeneous population.

Measures (1) the epidemic threshold: the R0 at which outbreaks start to take
off, expected near 1; and (2) the herd immunity threshold: the immune share at
which they stop taking off, expected near 1 - 1/R0.
"""

from __future__ import annotations

from collections.abc import Sequence

from engine.core.rng import Rng
from engine.domains.infectious.model import make_rates, simulate_single_population

POPULATION = 20000
INDEX_CASES = 5
REPLICATES = 200
TAKE_OFF = 0.01  # mean share of susceptibles infected that counts as "taking off"


def mean_attack_rate(r0: float, immune_share: float, label: str) -> float:
    """Mean share of initially susceptible people infected, over replicates."""
    params = {"infectious.r0": r0, "infectious.latent_weeks": 1.0,
              "infectious.infectious_weeks": 1.5, "infectious.case_fatality": 0.0}
    rates = make_rates(params)
    immune = round(POPULATION * immune_share)
    susceptible = POPULATION - immune - INDEX_CASES
    total = 0
    for replicate in range(REPLICATES):
        rng = Rng(f"sanity:{label}:{r0}:{immune_share}:{replicate}")
        total += simulate_single_population(POPULATION, immune, INDEX_CASES, rates, rng)
    return total / (REPLICATES * susceptible)


def crossing(xs: Sequence[float], ys: Sequence[float], level: float) -> float:
    """x at which y first crosses `level`, by linear interpolation (nan if never)."""
    for i in range(1, len(xs)):
        low, high = ys[i - 1], ys[i]
        if (low - level) * (high - level) <= 0 and low != high:
            return xs[i - 1] + (level - low) * (xs[i] - xs[i - 1]) / (high - low)
    return float("nan")


def epidemic_threshold() -> dict[str, object]:
    """Attack rate against R0 with nobody immune; where does it take off?"""
    grid = [0.6, 0.8, 0.9, 1.0, 1.1, 1.2, 1.5, 2.0]
    attack = [mean_attack_rate(r0, 0.0, "threshold") for r0 in grid]
    return {"r0_grid": grid, "mean_attack_rate": [round(a, 4) for a in attack],
            "measured_threshold_r0": round(crossing(grid, attack, TAKE_OFF), 3),
            "expected": 1.0}


def herd_immunity_threshold(r0: float) -> dict[str, object]:
    """Attack rate against immune share at a fixed R0; where does it stop taking off?"""
    expected = 1.0 - 1.0 / r0
    grid = [round(expected + step * 0.025, 4) for step in range(-6, 5)]
    attack = [mean_attack_rate(r0, share, "herd") for share in grid]
    return {"r0": r0, "immune_share_grid": grid,
            "mean_attack_rate": [round(a, 4) for a in attack],
            "measured_threshold": round(crossing(grid, attack, TAKE_OFF), 3),
            "expected": round(expected, 3)}
