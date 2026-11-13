"""Interactive game: one run in progress, played turn by turn.

Contract: after any number of turns, the game's event log equals the log of
`runner.run(content, seed, game.plays)` paused at the same tick (tested).
Budget and action points are turn accounting; they do not enter the simulation.
"""

from __future__ import annotations

from collections.abc import Sequence

from engine.actions.apply import check_target, valid_targets
from engine.actions.cards import Card
from engine.content import Content
from engine.core.events import Event
from engine.runner import Play, build_simulation, hand_for, play_turn


class InvalidPlayError(ValueError):
    """The chosen cards break a rule of the turn."""


class Game:
    """Turn state around a Simulation."""

    def __init__(self, content: Content, seed_text: str) -> None:
        self.content = content
        self.seed_text = seed_text
        self.sim = build_simulation(content, seed_text)
        self.turn = 0
        self.budget = int(content.theme["turn"]["budget_start"])
        self.plays: list[Play] = []
        self.feed_start = 0  # id of the first event of the most recent turn

    @property
    def finished(self) -> bool:
        """True after the last turn has been played."""
        return self.turn >= self.sim.clock.turns

    def hand(self) -> list[Card]:
        """Cards on offer this turn."""
        if self.finished:
            return []
        return hand_for(self.content, self.seed_text, self.turn)

    def targets(self, card: Card) -> list[str]:
        """Places the card may be played on."""
        return valid_targets(self.sim, card)

    def check(self, choices: Sequence[tuple[str, str]]) -> None:
        """Raise InvalidPlayError if the choices are not allowed this turn."""
        rules = self.content.theme["turn"]
        hand = {card.id: card for card in self.hand()}
        if self.finished:
            raise InvalidPlayError("the run is over")
        if len(choices) > int(rules["max_cards"]):
            raise InvalidPlayError(f"at most {rules['max_cards']} cards per turn")
        if len({card_id for card_id, _ in choices}) != len(choices):
            raise InvalidPlayError("each card can be played once per turn")
        budget, points = 0, 0
        for card_id, target in choices:
            if card_id not in hand:
                raise InvalidPlayError(f"card {card_id} is not in this turn's hand")
            if not check_target(hand[card_id], target) or target not in self.targets(hand[card_id]):
                raise InvalidPlayError(f"{target} is not a valid target for {card_id}")
            budget += hand[card_id].budget_cost
            points += hand[card_id].action_points
        if budget > self.budget:
            raise InvalidPlayError("not enough budget")
        if points > int(rules["action_points"]):
            raise InvalidPlayError("not enough action points")

    def play_turn(self, choices: Sequence[tuple[str, str]]) -> list[Event]:
        """Play the chosen cards, simulate to the next turn, return the new events."""
        self.check(choices)
        hand = {card.id: card for card in self.hand()}
        turn_plays = [Play(self.turn, card_id, target) for card_id, target in choices]
        self.budget -= sum(hand[play.card_id].budget_cost for play in turn_plays)
        self.plays.extend(turn_plays)
        self.feed_start = len(self.sim.log)
        play_turn(self.sim, self.content, self.turn, turn_plays)
        self.turn += 1
        if not self.finished:
            self.budget += int(self.content.theme["turn"]["budget_per_turn"])
        return [self.sim.log.get(i) for i in range(self.feed_start, len(self.sim.log))]
