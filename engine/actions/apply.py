"""Apply one played card to a running simulation (tick pipeline step 1)."""

from __future__ import annotations

from engine.actions.cards import Card
from engine.actions.handlers import HANDLERS
from engine.actions.ops import ActionContext, apply_effect
from engine.core.events import ACTION_KIND, Event
from engine.core.ids import DISTRICT_ID, is_block, is_village
from engine.core.pipeline import Simulation
from engine.core.rng import Rng


def valid_targets(sim: Simulation, card: Card) -> list[str]:
    """Place ids the card may be played on."""
    if card.target_kind == "village":
        return [village.id for village in sim.district.villages]
    if card.target_kind == "block":
        return [block.id for block in sim.district.blocks]
    return [DISTRICT_ID]


def check_target(card: Card, target: str) -> bool:
    """True if `target` has the right shape for the card."""
    if card.target_kind == "village":
        return is_village(target)
    if card.target_kind == "block":
        return is_block(target)
    return target == DISTRICT_ID


def apply_card(sim: Simulation, card: Card, target: str) -> Event:
    """Log the player action and apply the card's effects with its taint."""
    action = sim.log.append(sim.tick, ACTION_KIND, target, {"card": card.id}, (), "player")
    view = sim.state.player_view()
    view.begin_scope(action.id)
    rng = Rng(sim.seed_text).fork(f"action:{sim.tick}:{card.id}:{target}")
    ctx = ActionContext(sim.tick, sim.district, view, sim.log, sim.schedule, rng, sim.params,
                        action.id, target)
    for effect in card.effects:
        if effect["op"] == "handler":
            HANDLERS[effect["name"]](ctx)
        else:
            apply_effect(ctx, effect)
    return action
