"""The SEIR-type arithmetic, free of the state store so it can be tested alone.

One population, weekly steps:
  S -> E   each susceptible is infected with probability 1 - exp(-lambda),
           lambda = beta * contact_mult * effective_infectious / alive
  E -> I   with probability 1 - exp(-1 / latent_weeks)
  I -> R/D with probability 1 - exp(-1 / infectious_weeks); a share
           `case_fatality` of those leaving I die

beta is set so that one case in a fully susceptible population causes R0
secondary cases on average: beta = R0 * P(leave I per week).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from engine.core.domain import Params
from engine.core.rng import Rng


@dataclass(frozen=True)
class Rates:
    """Weekly transition rates derived from the parameters."""

    beta: float
    p_progress: float
    p_remove: float
    case_fatality: float
    herd_threshold: float


@dataclass(frozen=True)
class Flows:
    """People moving between compartments in one week."""

    new_exposed: int
    new_infectious: int
    removed: int
    deaths: int


def make_rates(params: Params) -> Rates:
    """Turn the content parameters into weekly probabilities."""
    r0 = params["infectious.r0"]
    p_remove = 1.0 - math.exp(-1.0 / params["infectious.infectious_weeks"])
    p_progress = 1.0 - math.exp(-1.0 / params["infectious.latent_weeks"])
    herd_threshold = max(0.0, 1.0 - 1.0 / r0) if r0 > 0 else 0.0
    return Rates(r0 * p_remove, p_progress, p_remove, params["infectious.case_fatality"],
                 herd_threshold)


def seir_flows(s: int, e: int, i: int, alive: int, effective_infectious: float,
               contact_mult: float, rates: Rates, rng: Rng) -> Flows:
    """Draw one week of transitions. Always consumes four random numbers."""
    force = 0.0
    if alive > 0:
        force = rates.beta * contact_mult * effective_infectious / alive
    new_exposed = rng.binomial(s, 1.0 - math.exp(-force))
    new_infectious = rng.binomial(e, rates.p_progress)
    removed = rng.binomial(i, rates.p_remove)
    deaths = rng.binomial(removed, rates.case_fatality)
    return Flows(new_exposed, new_infectious, removed, deaths)


def simulate_single_population(population: int, immune: int, index_cases: int, rates: Rates,
                               rng: Rng, max_weeks: int = 400) -> int:
    """Run one closed, homogeneous population until the infection dies out.

    Returns the number of people infected after the index cases. Used by the
    model-sanity tests (epidemic threshold, herd immunity threshold).
    """
    s = population - immune - index_cases
    e, i, infected = 0, index_cases, 0
    for week in range(max_weeks):
        if e + i == 0:
            break
        flows = seir_flows(s, e, i, population, float(i), 1.0, rates, rng.fork(str(week)))
        s -= flows.new_exposed
        e += flows.new_exposed - flows.new_infectious
        i += flows.new_infectious - flows.removed
        infected += flows.new_exposed
    return infected
