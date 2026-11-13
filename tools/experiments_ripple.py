"""Counterfactual, conservation, butterfly and balance experiments (process-pool workers)."""

from __future__ import annotations

from typing import Any

from engine.actions.apply import apply_card
from engine.core.pipeline import Simulation
from engine.results import compute_results
from engine.runner import build_simulation, run
from engine.scoring.diff import diff
from tools.experiments import load_content, random_game, single_random_play

COMPARTMENTS = ("infectious.S", "infectious.E", "infectious.I", "infectious.R", "infectious.VI",
                "infectious.D")
UNIT_INTERVAL_KEYS = ("systems.trust", "systems.rumour", "systems.surveillance",
                      "systems.vaccine_potency", "systems.morale", "infectious.tracing")


def counterfactual_worker(seed_text: str) -> dict[str, Any]:
    """One random card versus baseline: is every difference downstream of the action?"""
    content = load_content()
    play = single_random_play(content, seed_text)
    player = run(content, seed_text, [play])
    baseline = run(content, seed_text, [])
    result = diff(player, baseline)
    action_tick = (play.turn * int(content.theme["clock"]["ticks_per_run"])
                   // int(content.theme["clock"]["turns"]))
    untainted = [i for i in result.only_player if not player.log.is_tainted(i)]
    early = [i for i in result.only_player if player.log.get(i).tick < action_tick]
    early += [i for i in result.only_baseline if baseline.log.get(i).tick < action_tick]
    changed_cells = [(key, place) for key, cells in player.final_state.items()
                     for place, value in cells.items()
                     if baseline.final_state[key][place] != value]
    unexplained = [cell for cell in changed_cells if cell not in player.tainted_cells]
    empty = diff(baseline, run(content, seed_text, []))
    return {"seed": seed_text, "card": play.card_id, "ripple_size": result.ripple_size,
            "only_player": len(result.only_player), "untainted_player_only": len(untainted),
            "differences_before_action": len(early), "changed_cells": len(changed_cells),
            "changed_cells_without_taint": len(unexplained), "empty_diff_is_zero": empty.is_zero,
            "health": compute_results(content, player, baseline, False).health.total}


def check_conservation(sim: Simulation) -> list[str]:
    """Problems found in the current state (empty list = all invariants hold)."""
    problems: list[str] = []
    peek = sim.state.peek
    for village in sim.district.villages:
        counts = [int(peek(key, village.id)) for key in COMPARTMENTS]
        if min(counts) < 0:
            problems.append(f"tick {sim.tick}: negative compartment in {village.id}")
        if sum(counts) != village.population:
            problems.append(f"tick {sim.tick}: population of {village.id} not conserved")
        if int(peek("infectious.vaccinated", village.id)) > village.population:
            problems.append(f"tick {sim.tick}: more vaccinated than people in {village.id}")
    for block in sim.district.blocks:
        if int(peek("systems.vaccine_stock", block.id)) < 0:
            problems.append(f"tick {sim.tick}: negative stock in {block.id}")
    for key in UNIT_INTERVAL_KEYS:
        for place in sim.state.places(key):
            if not 0.0 <= float(peek(key, place)) <= 1.0:
                problems.append(f"tick {sim.tick}: {key}[{place}] outside 0..1")
    return problems


def conservation_worker(seed_text: str) -> dict[str, Any]:
    """Replay a random game tick by tick, checking the invariants after every tick."""
    content = load_content()
    plays = random_game(content, seed_text, "a").plays
    sim = build_simulation(content, seed_text)
    problems = check_conservation(sim)
    doses_given = 0
    for turn in range(sim.clock.turns):
        for play in plays:
            if play.turn == turn:
                apply_card(sim, content.cards[play.card_id], play.target)
                problems += check_conservation(sim)
        while sim.tick < sim.clock.turn_start(turn + 1):
            sim.advance()
            problems += check_conservation(sim)
            doses_given += int(sim.state.totals()["systems.session_doses"])
    return {"seed": seed_text, "ticks": sim.tick, "problems": problems[:5],
            "doses_given": doses_given}


def butterfly_worker(seed_text: str) -> dict[str, Any]:
    """Ripple size of one random card on one seed."""
    row = counterfactual_worker(seed_text)
    return {"seed": seed_text, "card": row["card"], "ripple_size": row["ripple_size"],
            "health": row["health"]}


def balance_worker(seed_text: str) -> list[dict[str, Any]]:
    """Four random-policy games on one seed, scored against the shared baseline."""
    content = load_content()
    baseline = run(content, seed_text, [])
    rows = []
    for policy in ("p1", "p2", "p3", "p4"):
        game = random_game(content, seed_text, policy)
        results = compute_results(content, game.sim.result(), baseline, False)
        rows.append({"seed": seed_text, "policy": policy, "score": results.health.total,
                     "cards": [play.card_id for play in game.plays]})
    return rows
