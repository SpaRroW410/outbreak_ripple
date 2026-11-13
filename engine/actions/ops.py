"""Declarative effect operations for action cards (SDD section 6).

Each effect is a JSON object with an "op":
  set_state       {key, where, value}
  add_state       {key, where, amount, min?, max?}
  schedule_event  {delay, kind, where, payload}
  inject_rumour   {where, amount}
  handler         {name}            -> a function in handlers.py

"where" picks the places an effect applies to, relative to the card's target:
  target      the chosen place itself
  villages    the villages of the target (itself if it is a village)
  neighbours  the neighbouring villages of a target village
  block       the block of the target (itself if it is a block)
  blocks      every block of the district
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from engine.core.district import District
from engine.core.domain import Params
from engine.core.events import Event, EventLog, Payload
from engine.core.ids import DISTRICT_ID, block_of, is_block, is_village
from engine.core.rng import Rng
from engine.core.schedule import Schedule, ScheduledEvent
from engine.core.state import StateView

OPS = ("set_state", "add_state", "schedule_event", "inject_rumour", "handler")
WHERE = ("target", "villages", "neighbours", "block", "blocks")
RUMOUR_KEY = "systems.rumour"


@dataclass
class ActionContext:
    """What an effect may use. All writes carry the action's taint."""

    tick: int
    district: District
    state: StateView  # the unrestricted player view
    log: EventLog
    schedule_queue: Schedule
    rng: Rng
    params: Params
    action_id: int
    target: str

    def emit(self, kind: str, place_id: str, payload: Payload) -> Event:
        """Log a visible consequence of the card, caused by the action."""
        if not kind.startswith("actions."):
            raise ValueError("card handlers emit events named actions.*")
        event = self.log.append(self.tick, kind, place_id, payload, [self.action_id], "actions")
        self.state.mark(event.id)
        return event

    def schedule(self, delay: int, kind: str, place_id: str, payload: Payload) -> None:
        """Queue a delayed effect for a domain, caused by the action."""
        cause = self.state.scope_taint
        causes = (self.action_id if cause is None else cause,)
        self.schedule_queue.add(ScheduledEvent(self.tick + delay, kind, place_id, dict(payload),
                                               causes))


def resolve_places(district: District, target: str, where: str) -> list[str]:
    """Place ids selected by `where`, sorted."""
    if where == "target":
        return [target]
    if where == "blocks":
        return [block.id for block in district.blocks]
    if where == "block":
        return [DISTRICT_ID] if target == DISTRICT_ID else [block_of(target)]
    if where == "villages":
        if is_village(target):
            return [target]
        if is_block(target):
            return list(district.block(target).village_ids)
        return [village.id for village in district.villages]
    if where == "neighbours":
        return list(district.village(target).neighbours) if is_village(target) else []
    raise ValueError(f"unknown where: {where!r}")


def apply_effect(ctx: ActionContext, effect: Mapping[str, Any]) -> None:
    """Apply one declarative effect (handlers are dispatched by the caller)."""
    op = effect["op"]
    places = resolve_places(ctx.district, ctx.target, effect.get("where", "target"))
    for place in places:
        if op == "set_state":
            ctx.state.set(effect["key"], place, effect["value"])
        elif op == "add_state":
            ctx.state.add(effect["key"], place, effect["amount"], effect.get("min"),
                          effect.get("max"))
        elif op == "inject_rumour":
            ctx.state.add(RUMOUR_KEY, place, effect["amount"], 0.0, 1.0)
        elif op == "schedule_event":
            ctx.schedule(int(effect["delay"]), effect["kind"], place, effect.get("payload", {}))
        else:
            raise ValueError(f"unknown effect op: {op!r}")
