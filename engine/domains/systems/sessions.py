"""Vaccination sessions: routine outreach every few weeks plus campaign doses.

Demand depends on trust and rumours, supply on session capacity (staff) and
block stock. The doses actually given are written to `systems.session_doses`;
the infectious domain turns doses into immunity.
"""

from __future__ import annotations

from engine.core.district import Village
from engine.core.domain import TickContext
from engine.core.rng import Rng
from engine.domains.systems import keys as k


def run_session(ctx: TickContext, village: Village, rng: Rng) -> None:
    """Work out this week's doses for one village and draw them from block stock."""
    state, params = ctx.state, ctx.params
    vid, bid = village.id, village.block_id
    interval = int(params["systems.session_interval_weeks"])
    offset = state.count(k.SESSION_OFFSET, vid)
    boost = state.num(k.SESSION_BOOST, vid)
    campaign = state.count(k.CAMPAIGN_DOSES, vid)
    trust = state.num(k.TRUST, vid)
    rumour = state.num(k.RUMOUR, vid)
    stock = state.count(k.VACCINE_STOCK, bid)
    stocked_out = state.count(k.STOCKED_OUT, bid)
    stock_cause = state.count(k.STOCK_CAUSE, bid)
    vaccinated = int(state.get_or(k.INF_VACCINATED, vid, 0))
    eligible = max(0, village.population - vaccinated)
    acceptance = trust * (1.0 - rumour)
    is_session_week = (ctx.tick + offset) % interval == 0

    routine_probability = params["systems.session_uptake"] * acceptance * boost
    routine_wanted = rng.binomial(eligible, min(1.0, routine_probability))
    campaign_probability = params["systems.campaign_uptake"] * acceptance
    campaign_wanted = rng.binomial(eligible, min(1.0, campaign_probability))
    capacity = 0.0
    wanted = 0
    if is_session_week:
        capacity = village.population * params["systems.session_capacity_per_1000"] / 1000
        capacity *= _capacity_factor(ctx, bid)
        wanted = routine_wanted
        boost = 1.0  # a one-off boost is used up by the session
    wanted += min(campaign, campaign_wanted)
    capacity += campaign
    doses = min(wanted, int(capacity), stock)
    if wanted > 0 and stock == 0:
        if stocked_out == 0:
            stocked_out = 1
            event = ctx.emit("systems.stockout", bid, {}, [stock_cause])
            stock_cause = event.id
        ctx.emit("systems.session_missed", vid, {"wanted": wanted}, [stock_cause])
    state.set(k.SESSION_DOSES, vid, doses)
    state.set(k.CAMPAIGN_DOSES, vid, 0)
    state.set(k.SESSION_BOOST, vid, boost)
    state.set(k.VACCINE_STOCK, bid, stock - doses)
    state.set(k.STOCKED_OUT, bid, stocked_out)
    state.set(k.STOCK_CAUSE, bid, stock_cause)


def _capacity_factor(ctx: TickContext, block_id: str) -> float:
    """Overloaded or demoralised staff run smaller sessions."""
    overloaded = ctx.state.count(k.OVERLOADED, block_id)
    morale = ctx.state.num(k.MORALE, block_id)
    factor = 0.6 + 0.4 * morale
    if overloaded == 1:
        factor *= ctx.params["systems.overload_capacity_factor"]
    return factor
