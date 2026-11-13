"""Build and replay runs: `run(content, seed, plays)` is the counterfactual engine's core.

Contract (SDD 4.6): the same seed and the same plays give an identical event
log. `run(content, seed, [])` is the no-action baseline. `noise` selects a
different set of dynamics streams for the same district (used for "surprise").
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from engine.actions.apply import apply_card
from engine.actions.cards import Card
from engine.content import Content
from engine.core.clock import Clock
from engine.core.pipeline import RunResult, Simulation
from engine.core.rng import Rng
from engine.registry import build_domains
from engine.world.generator import generate_district


@dataclass(frozen=True)
class Play:
    """One card played on one target at the start of a turn."""

    turn: int
    card_id: str
    target: str


def make_clock(content: Content) -> Clock:
    """Clock from the theme."""
    clock = content.theme["clock"]
    return Clock(int(clock["ticks_per_run"]), int(clock["turns"]))


def build_simulation(content: Content, seed_text: str, noise: int = 0) -> Simulation:
    """A fresh simulation at tick 0 for this seed."""
    district = generate_district(Rng(seed_text).fork("world"), content.theme["world"],
                                 content.params)
    return Simulation(district, build_domains(), content.params, seed_text,
                      make_clock(content), noise)


def hand_for(content: Content, seed_text: str, turn: int) -> list[Card]:
    """The cards offered in a turn. Depends only on seed and turn number."""
    size = int(content.theme["turn"]["hand_size"])
    card_ids = sorted(content.cards)
    chosen = Rng(seed_text).fork(f"hand:{turn}").sample(card_ids, min(size, len(card_ids)))
    return [content.cards[card_id] for card_id in sorted(chosen)]


def play_turn(sim: Simulation, content: Content, turn: int, plays: Sequence[Play]) -> None:
    """Apply this turn's cards (in the order given), then simulate to the next turn."""
    for play in plays:
        if play.turn == turn:
            apply_card(sim, content.cards[play.card_id], play.target)
    sim.advance_to(sim.clock.turn_start(turn + 1))


def run(content: Content, seed_text: str, plays: Sequence[Play], noise: int = 0) -> RunResult:
    """Simulate a whole run with the given plays."""
    sim = build_simulation(content, seed_text, noise)
    for turn in range(sim.clock.turns):
        play_turn(sim, content, turn, plays)
    return sim.result()
