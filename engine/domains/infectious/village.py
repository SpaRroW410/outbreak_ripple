"""Weekly update of one village: arrivals, vaccination, transmission, reporting.

Every cell is written every week, even when its value does not change; the
taint rule in `core/state.py` depends on that.
"""

from __future__ import annotations

from engine.core.district import Village
from engine.core.domain import TickContext
from engine.core.rng import Rng
from engine.domains.infectious import keys as k
from engine.domains.infectious.model import Rates, seir_flows
from engine.domains.infectious.reporting import report_cases

DEATH_MILESTONES = (1, 5, 10, 25, 50, 100, 250, 500, 1000)


def emit_here(ctx: TickContext, village_id: str, kind: str, payload: dict[str, int],
              cause: int) -> int:
    """Emit a disease event in a village and remember it as the latest one there."""
    event = ctx.emit(kind, village_id, payload, [cause])
    ctx.state.set(k.LAST_EVENT, village_id, event.id)
    return event.id


def step_village(ctx: TickContext, village: Village, rates: Rates) -> None:
    """Advance one village by one week. The caller has opened a scope."""
    rng = ctx.rng.fork(f"{village.id}:{ctx.tick}")
    _arrivals(ctx, village, rng)
    _vaccinate(ctx, village, rates, rng)
    new_cases = _transmit(ctx, village, rates, rng)
    report_cases(ctx, village, new_cases, rng)
    _milestones(ctx, village)
    last = ctx.state.count(k.LAST_EVENT, village.id)
    ctx.state.set(k.LAST_EVENT, village.id, last)  # refresh taint (see module docstring)


def _arrivals(ctx: TickContext, village: Village, rng: Rng) -> None:
    """Infected travellers from neighbours, index cases and outside importations."""
    state, params = ctx.state, ctx.params
    vid = village.id
    external = rng.chance(params["infectious.external_import_probability"])
    s, e, i = state.count(k.S, vid), state.count(k.E, vid), state.count(k.I, vid)
    incoming = state.count(k.INCOMING, vid)
    incoming_cause = state.count(k.INCOMING_CAUSE, vid)
    seed_tick = state.count(k.SEED_TICK, vid)
    moved = min(incoming, s)
    if moved > 0 and e + i == 0:
        emit_here(ctx, vid, "infectious.importation", {"cases": moved}, incoming_cause)
    seeded = 0
    if ctx.tick == seed_tick:
        seeded = int(params["infectious.index_cases"])
    elif external:
        seeded = 1
    seeded = min(seeded, s - moved)
    if seeded > 0:
        emit_here(ctx, vid, "infectious.index_case", {"cases": seeded}, ctx.genesis_id)
    state.set(k.S, vid, s - moved - seeded)
    state.set(k.E, vid, e + moved + seeded)
    state.set(k.INCOMING, vid, 0)


def _vaccinate(ctx: TickContext, village: Village, rates: Rates, rng: Rng) -> None:
    """Turn this week's doses (decided by the systems domain) into immunity."""
    state, params = ctx.state, ctx.params
    vid = village.id
    doses = int(state.get_or(k.SYS_SESSION_DOSES, vid, 0))
    potency = float(state.get_or(k.SYS_VACCINE_POTENCY, village.block_id, 1.0))
    s, vi = state.count(k.S, vid), state.count(k.VI, vid)
    vaccinated = state.count(k.VACCINATED, vid)
    alive = village.population - state.count(k.D, vid)
    eligible = max(0, alive - vaccinated)
    used = min(doses, eligible)
    susceptible_share = min(1.0, s / eligible) if eligible > 0 else 0.0
    reached = rng.binomial(used, susceptible_share)
    immunised = rng.binomial(reached, params["infectious.vaccine_efficacy"] * potency)
    immunised = min(immunised, s)
    state.set(k.S, vid, s - immunised)
    state.set(k.VI, vid, vi + immunised)
    state.set(k.VACCINATED, vid, vaccinated + used)
    protected = state.count(k.PROTECTED, vid)
    immune = vi + immunised + state.count(k.R, vid)
    if protected == 0 and alive > 0 and immune >= rates.herd_threshold * alive:
        protected = 1
        emit_here(ctx, vid, "infectious.herd_threshold_reached",
                  {"immune_percent": round(100 * immune / alive)},
                  state.count(k.LAST_EVENT, vid))
    state.set(k.PROTECTED, vid, protected)


def _transmit(ctx: TickContext, village: Village, rates: Rates, rng: Rng) -> int:
    """One week of S -> E -> I -> R/D. Returns the number of new infectious cases."""
    state, params = ctx.state, ctx.params
    vid = village.id
    s, e, i = state.count(k.S, vid), state.count(k.E, vid), state.count(k.I, vid)
    r, d = state.count(k.R, vid), state.count(k.D, vid)
    tracing = state.num(k.TRACING, vid)
    contact_mult = state.num(k.CONTACT_MULT, vid)
    trust = float(state.get_or(k.SYS_TRUST, vid, 0.6))
    effective = i * (1.0 - tracing * trust)
    flows = seir_flows(s, e, i, village.population - d, effective, contact_mult, rates, rng)
    state.set(k.S, vid, s - flows.new_exposed)
    state.set(k.E, vid, e + flows.new_exposed - flows.new_infectious)
    state.set(k.I, vid, i + flows.new_infectious - flows.removed)
    state.set(k.R, vid, r + flows.removed - flows.deaths)
    state.set(k.D, vid, d + flows.deaths)
    state.add(k.CUM_CASES, vid, flows.new_infectious)
    retained = params["infectious.tracing_retained_per_week"]
    state.set(k.TRACING, vid, round(tracing * retained, 4))
    state.set(k.CONTACT_MULT, vid, contact_mult)
    return flows.new_infectious


def _milestones(ctx: TickContext, village: Village) -> None:
    """Death milestones and the end of a declared outbreak."""
    state = ctx.state
    vid = village.id
    deaths = state.count(k.D, vid)
    index = state.count(k.DEATH_MILESTONE, vid)
    if index < len(DEATH_MILESTONES) and deaths >= DEATH_MILESTONES[index]:
        while index < len(DEATH_MILESTONES) and deaths >= DEATH_MILESTONES[index]:
            index += 1
        emit_here(ctx, vid, "infectious.death_milestone", {"deaths": deaths},
                  state.count(k.LAST_EVENT, vid))
    state.set(k.DEATH_MILESTONE, vid, index)
    declared = state.count(k.OUTBREAK_EVENT, vid)
    over = state.count(k.OUTBREAK_OVER, vid)
    active = state.count(k.E, vid) + state.count(k.I, vid) + state.count(k.PENDING_REPORTS, vid)
    if declared > 0 and over == 0 and active == 0:
        over = 1
        emit_here(ctx, vid, "infectious.outbreak_over",
                  {"cases": state.count(k.REPORTED_CASES, vid)}, declared)
    state.set(k.OUTBREAK_OVER, vid, over)
