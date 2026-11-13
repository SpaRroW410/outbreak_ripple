"""Simulation experiments shared by the invariant tests and the quality report.

Every worker function takes one picklable argument and returns plain data, so
it can run in a process pool (`pmap`). Content is loaded once per process.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor
from typing import Any

from engine.content import Content, parse_content
from engine.core.pipeline import RunResult
from engine.core.rng import Rng
from engine.game import Game
from engine.runner import Play, run
from tools.content_io import load_bundle

_CONTENT: dict[str, Content] = {}

SMALL_WORLD = {"blocks_min": 2, "blocks_max": 2, "villages_min": 3, "villages_max": 3}


def load_content(small: bool = False) -> Content:
    """The repository content; `small=True` shrinks the district for brute-force tests."""
    key = "small" if small else "default"
    if key not in _CONTENT:
        bundle = load_bundle()
        if small:
            bundle["themes"]["default"]["world"].update(SMALL_WORLD)
        _CONTENT[key] = parse_content(bundle)
    return _CONTENT[key]


def pmap[T, U](function: Callable[[T], U], items: Sequence[T]) -> list[U]:
    """Map over items in a process pool, keeping order."""
    workers = min(len(items), os.cpu_count() or 1)
    if workers <= 1:
        return [function(item) for item in items]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(function, items, chunksize=max(1, len(items) // (workers * 4))))


def random_game(content: Content, seed_text: str, policy: str) -> Game:
    """Play a whole game with a random but legal policy named by `policy`."""
    game = Game(content, seed_text)
    rng = Rng(seed_text).fork(f"policy:{policy}")
    rules = content.theme["turn"]
    while not game.finished:
        hand = game.hand()
        rng.shuffle(hand)
        wanted = rng.choice([0, 1, 1, 2, 2, 2])
        choices: list[tuple[str, str]] = []
        budget, points = game.budget, int(rules["action_points"])
        for card in hand:
            if len(choices) == wanted:
                break
            if card.budget_cost <= budget and card.action_points <= points:
                choices.append((card.id, rng.choice(game.targets(card))))
                budget -= card.budget_cost
                points -= card.action_points
        game.play_turn(choices)
    return game


def single_random_play(content: Content, seed_text: str) -> Play:
    """One random card from a random turn's hand on a random target."""
    rng = Rng(seed_text).fork("single-play")
    turn = rng.randrange(int(content.theme["clock"]["turns"]))
    game = Game(content, seed_text)
    game.turn = turn  # only to ask for that turn's hand and targets
    card = rng.choice(game.hand())
    return Play(turn, card.id, rng.choice(game.targets(card)))


def determinism_worker(seed_text: str) -> dict[str, Any]:
    """Random game twice plus a replay through `run`; returns the three digests."""
    content = load_content()
    first = random_game(content, seed_text, "a")
    second = random_game(content, seed_text, "a")
    replay = run(content, seed_text, first.plays)
    return {"seed": seed_text, "events": len(first.sim.log),
            "digests": [first.sim.log.digest(), second.sim.log.digest(), replay.log.digest()],
            "states_equal": first.sim.state.snapshot() == second.sim.state.snapshot()
            == replay.final_state}


def played_result(seed_text: str, small: bool = False) -> RunResult:
    """Result of a random game (helper for causality tests)."""
    return random_game(load_content(small), seed_text, "a").sim.result()
