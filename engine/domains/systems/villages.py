"""Village-level weekly update: rumours, trust, surveillance, vaccination sessions."""

from __future__ import annotations

from engine.core.district import Village
from engine.core.domain import TickContext
from engine.domains.systems import keys as k
from engine.domains.systems.sessions import run_session


def step_village(ctx: TickContext, village: Village) -> None:
    """Advance one village by one week. The caller has opened a scope."""
    rng = ctx.rng.fork(f"{village.id}:{ctx.tick}")
    aefi_draw = rng.random()
    _react_to_disease(ctx, village)
    _aefi_rumour(ctx, village, aefi_draw)
    _rumour_and_trust(ctx, village)
    state = ctx.state
    retained = ctx.params["systems.surveillance_retained_per_week"]
    boost = state.num(k.SURVEILLANCE, village.id) * retained
    state.set(k.SURVEILLANCE, village.id, round(boost, 4))
    run_session(ctx, village, rng)


def _react_to_disease(ctx: TickContext, village: Village) -> None:
    """A declared outbreak and new deaths feed rumours."""
    state, params = ctx.state, ctx.params
    vid = village.id
    outbreak = int(state.get_or(k.INF_OUTBREAK_EVENT, vid, 0))
    deaths = int(state.get_or(k.INF_DEATHS, vid, 0))
    seen_outbreak = state.count(k.SEEN_OUTBREAK, vid)
    seen_deaths = state.count(k.SEEN_DEATHS, vid)
    trust = state.num(k.TRUST, vid)
    cause = state.count(k.RUMOUR_CAUSE, vid)
    bump = 0.0
    if outbreak != seen_outbreak:
        bump += params["systems.rumour_bump_outbreak"] * (1.0 - trust)
        cause = outbreak
    bump += params["systems.rumour_bump_per_death"] * max(0, deaths - seen_deaths)
    state.add(k.RUMOUR, vid, bump, 0.0, 1.0)
    state.set(k.RUMOUR_CAUSE, vid, cause)
    state.set(k.SEEN_OUTBREAK, vid, outbreak)
    state.set(k.SEEN_DEATHS, vid, deaths)


def _aefi_rumour(ctx: TickContext, village: Village, draw: float) -> None:
    """Now and then a session is followed by a scare about side effects."""
    state, params = ctx.state, ctx.params
    doses_last_week = state.count(k.SESSION_DOSES, village.id)
    cause = state.count(k.RUMOUR_CAUSE, village.id)
    bump = 0.0
    if doses_last_week > 0 and draw < params["systems.aefi_rumour_probability"]:
        event = ctx.emit("systems.aefi_rumour", village.id, {}, [ctx.genesis_id])
        bump = params["systems.aefi_rumour_bump"]
        cause = event.id
    state.add(k.RUMOUR, village.id, bump, 0.0, 1.0)
    state.set(k.RUMOUR_CAUSE, village.id, cause)


def _rumour_and_trust(ctx: TickContext, village: Village) -> None:
    """Rumours grow where trust is low; rumours erode trust; both have tipping points."""
    state, params = ctx.state, ctx.params
    vid = village.id
    rumour = state.num(k.RUMOUR, vid)
    trust = state.num(k.TRUST, vid)
    base = state.num(k.TRUST_BASE, vid)
    high = state.count(k.RUMOUR_HIGH, vid)
    low = state.count(k.TRUST_LOW, vid)
    cause = state.count(k.RUMOUR_CAUSE, vid)
    rumour += params["systems.rumour_growth_rate"] * rumour * (1.0 - rumour) * (1.0 - trust)
    rumour -= params["systems.rumour_decay_rate"] * rumour * trust
    rumour = min(1.0, max(0.0, rumour))
    trust += params["systems.trust_recovery_rate"] * (base - trust)
    trust -= params["systems.trust_erosion_per_rumour"] * rumour
    trust = min(1.0, max(0.0, trust))
    if high == 0 and rumour >= params["systems.rumour_surge_threshold"]:
        high = 1
        event = ctx.emit("systems.rumour_surge", vid, {"rumour": round(rumour, 2)}, [cause])
        cause = event.id
        for neighbour in village.neighbours:
            ctx.schedule(1, "systems.rumour_spread", neighbour,
                         {"amount": params["systems.rumour_spread_amount"]}, [event.id])
    elif high == 1 and rumour < params["systems.rumour_calm_threshold"]:
        high = 0
    if low == 0 and trust < params["systems.trust_collapse_threshold"]:
        low = 1
        ctx.emit("systems.trust_collapse", vid, {"trust": round(trust, 2)}, [cause])
    elif low == 1 and trust > params["systems.trust_recovered_threshold"]:
        low = 0
        ctx.emit("systems.trust_recovered", vid, {"trust": round(trust, 2)}, [cause])
    for neighbour in village.neighbours:
        state.add(k.RUMOUR, neighbour, 0.0)  # no change; carries taint (see core/state.py)
    state.set(k.RUMOUR, vid, round(rumour, 4))
    state.set(k.TRUST, vid, round(trust, 4))
    state.set(k.RUMOUR_HIGH, vid, high)
    state.set(k.TRUST_LOW, vid, low)
    state.set(k.RUMOUR_CAUSE, vid, cause)
