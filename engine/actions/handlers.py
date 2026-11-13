"""Named handlers for card behaviour that plain effect ops cannot express.

Rules (SDD section 6): each handler is at most 40 lines (checked by
tools/check_sizes.py), takes an ActionContext, and is listed in HANDLERS.
Most handlers belong to "meddle" cards: small nudges with uncertain results.
"""

from __future__ import annotations

from collections.abc import Callable

from engine.actions.ops import ActionContext
from engine.domains.infectious import keys as inf
from engine.domains.systems import keys as sys


def reschedule_session(ctx: ActionContext) -> None:
    """Move the next routine session to this week; it may clash with a local event."""
    village = ctx.target
    interval = int(ctx.params["systems.session_interval_weeks"])
    if ctx.rng.chance(0.55):
        ctx.state.set(sys.SESSION_OFFSET, village, (-ctx.tick) % interval)
        ctx.state.set(sys.SESSION_BOOST, village, 1.8)
        ctx.emit("actions.session_well_timed", village, {})
    else:
        ctx.state.set(sys.SESSION_OFFSET, village, (-ctx.tick - 1) % interval)
        ctx.state.set(sys.SESSION_BOOST, village, 0.2)
        ctx.state.add(sys.TRUST, village, -0.06, 0.0, 1.0)
        ctx.emit("actions.session_clash", village, {})


def redirect_stock(ctx: ActionContext) -> None:
    """Send half of this block's vaccine stock to the block with the least stock per person."""
    source = ctx.target
    others = [block.id for block in ctx.district.blocks if block.id != source]
    if not others:
        return
    def stock_per_person(block_id: str) -> float:
        stock = ctx.state.count(sys.VACCINE_STOCK, block_id)
        return stock / ctx.district.block_population(block_id)
    destination = min(others, key=lambda block_id: (stock_per_person(block_id), block_id))
    doses = ctx.state.count(sys.VACCINE_STOCK, source) // 2
    ctx.state.add(sys.VACCINE_STOCK, source, -doses)
    ctx.state.add(sys.VACCINE_STOCK, destination, doses)
    event = ctx.emit("actions.stock_redirected", destination, {"doses": doses})
    ctx.state.set(sys.STOCK_CAUSE, source, event.id)
    ctx.state.set(sys.STOCK_CAUSE, destination, event.id)


def press_note(ctx: ActionContext) -> None:
    """A press note calms the district if trust is high, or is misread and spreads alarm."""
    villages = [village.id for village in ctx.district.villages]
    mean_trust = sum(ctx.state.num(sys.TRUST, vid) for vid in villages) / len(villages)
    if ctx.rng.chance(mean_trust):
        for vid in villages:
            ctx.state.add(sys.RUMOUR, vid, -0.08, 0.0, 1.0)
            ctx.state.add(sys.TRUST, vid, 0.02, 0.0, 1.0)
        ctx.emit("actions.press_note_calms", ctx.target, {})
        return
    alarmed = sorted(ctx.rng.sample(villages, min(4, len(villages))))
    event = ctx.emit("actions.press_note_backfires", ctx.target, {"villages": len(alarmed)})
    for vid in alarmed:
        ctx.state.add(sys.RUMOUR, vid, 0.3, 0.0, 1.0)
        ctx.state.set(sys.RUMOUR_CAUSE, vid, event.id)


def transfer_mo(ctx: ActionContext) -> None:
    """Move a medical officer from this block to the block with the highest workload."""
    source = ctx.target
    others = [block.id for block in ctx.district.blocks if block.id != source]
    if not others:
        return
    destination = max(others, key=lambda bid: (ctx.state.num(sys.WORKLOAD, bid), bid))
    ctx.state.add(sys.STAFF, source, -0.3, 0.3, 3.0)
    ctx.state.add(sys.MORALE, source, -0.1, 0.0, 1.0)
    ctx.state.add(sys.STAFF, destination, 0.3, 0.3, 3.0)
    ctx.emit("actions.mo_transferred", destination, {})


def surprise_inspection(ctx: ActionContext) -> None:
    """An unannounced visit tightens discipline, or is resented and staff stay away."""
    block = ctx.target
    if ctx.rng.chance(0.6):
        ctx.state.add(sys.COLD_CHAIN_CARE, block, 12)
        for vid in ctx.district.block(block).village_ids:
            ctx.state.add(sys.SURVEILLANCE, vid, 0.25, 0.0, 1.0)
        ctx.emit("actions.inspection_tightens", block, {})
    else:
        ctx.state.add(sys.MORALE, block, -0.25, 0.0, 1.0)
        ctx.state.add(sys.STAFF, block, -0.2, 0.3, 3.0)
        ctx.emit("actions.inspection_resented", block, {})


def flush_reports(ctx: ActionContext) -> None:
    """An investigation team builds a line list: pending cases are reported at once."""
    village = ctx.target
    pending = ctx.state.count(inf.PENDING_REPORTS, village)
    ctx.state.set(inf.PENDING_REPORTS, village, 0)
    ctx.state.add(inf.REPORTED_CASES, village, pending)
    ctx.state.add(inf.REPORTED_WEEK, village, pending)
    ctx.emit("actions.line_list_completed", village, {"cases": pending})


HANDLERS: dict[str, Callable[[ActionContext], None]] = {
    "reschedule_session": reschedule_session,
    "redirect_stock": redirect_stock,
    "press_note": press_note,
    "transfer_mo": transfer_mo,
    "surprise_inspection": surprise_inspection,
    "flush_reports": flush_reports,
}
