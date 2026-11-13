"""Travel of infectious people between neighbouring villages.

Runs after all villages have been updated; arrivals are picked up by the
destination village in the next week. The destination cells are written even
when nobody travels, so that the taint rule in `core/state.py` holds.
"""

from __future__ import annotations

from engine.core.district import Village
from engine.core.domain import TickContext
from engine.domains.infectious import keys as k


def export_travellers(ctx: TickContext, village: Village) -> None:
    """Draw infected travellers from `village` to each neighbour."""
    state = ctx.state
    rng = ctx.rng.fork(f"travel:{village.id}:{ctx.tick}")
    infectious = state.count(k.I, village.id)
    tracing = state.num(k.TRACING, village.id)
    trust = float(state.get_or(k.SYS_TRUST, village.id, 0.6))
    source_event = state.count(k.LAST_EVENT, village.id)
    rate = ctx.params["infectious.travel_rate"] * (1.0 - tracing * trust)
    for neighbour in village.neighbours:
        travellers = rng.binomial(infectious, rate)
        cause = state.count(k.INCOMING_CAUSE, neighbour)
        state.add(k.INCOMING, neighbour, travellers)
        state.set(k.INCOMING_CAUSE, neighbour, source_event if travellers > 0 else cause)
