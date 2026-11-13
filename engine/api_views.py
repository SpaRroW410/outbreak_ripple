"""Builds the JSON-ready dicts returned by the API (see docs/API.md)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import Any

from engine.content import Content
from engine.core.events import Event
from engine.core.graph import ancestors
from engine.game import Game
from engine.results import Results

MAX_CHAIN_NODES = 200


def _place_names(game: Game) -> dict[str, str]:
    names = {"D": game.sim.district.name}
    for block in game.sim.district.blocks:
        names[block.id] = block.name
    for village in game.sim.district.villages:
        names[village.id] = village.name
    return names


def event_view(event: Event, names: dict[str, str]) -> dict[str, Any]:
    """An event plus the display name of its place."""
    view = event.to_dict()
    view["place_name"] = names.get(event.place_id, event.place_id)
    return view


def state_view(game: Game, feed: Sequence[Event]) -> dict[str, Any]:
    """What the player may see: reported cases, deaths, coverage, mood, stock."""
    peek = game.sim.state.peek
    names = _place_names(game)
    blocks: list[dict[str, Any]] = []
    all_villages: list[dict[str, Any]] = []
    for block in game.sim.district.blocks:
        villages: list[dict[str, Any]] = []
        for village in game.sim.district.villages_in(block.id):
            villages.append({
                "id": village.id, "name": village.name, "kind": village.kind,
                "population": village.population,
                "reported_cases": peek("infectious.reported_cases", village.id),
                "reported_week": peek("infectious.reported_week", village.id),
                "deaths": peek("infectious.D", village.id),
                "coverage": round(float(peek("infectious.vaccinated", village.id))
                                  / village.population, 3),
                "trust": peek("systems.trust", village.id),
                "rumour": peek("systems.rumour", village.id),
                "outbreak": int(peek("infectious.outbreak_event", village.id)) > 0
                and int(peek("infectious.outbreak_over", village.id)) == 0,
            })
        all_villages.extend(villages)
        blocks.append({
            "id": block.id, "name": block.name, "villages": villages,
            "vaccine_stock": peek("systems.vaccine_stock", block.id),
            "cold_chain_ok": int(peek("systems.cold_chain_ok", block.id)) == 1,
            "overloaded": int(peek("systems.overloaded", block.id)) == 1,
        })
    rules = game.content.theme["turn"]
    hidden = set(game.content.theme.get("feed_hidden_kinds", []))  # the DHO cannot see these
    return {
        "seed": game.seed_text, "turn": game.turn, "turns": game.sim.clock.turns,
        "tick": game.sim.tick, "ticks": game.sim.clock.ticks_per_run, "finished": game.finished,
        "budget": game.budget, "action_points": int(rules["action_points"]),
        "max_cards": int(rules["max_cards"]),
        "theme": {"title": game.content.theme["title"],
                  "disease_name": game.content.theme["disease_name"],
                  "disease_note": game.content.theme["disease_note"]},
        "district": {"name": game.sim.district.name,
                     "population": game.sim.district.population, "blocks": blocks},
        "totals": {
            "reported_cases": sum(int(v["reported_cases"]) for v in all_villages),
            "deaths": sum(int(v["deaths"]) for v in all_villages),
            "coverage": round(sum(float(v["coverage"]) * int(v["population"])
                                  for v in all_villages) / game.sim.district.population, 3),
        },
        "hand": [card.to_dict() for card in game.hand()],
        "feed": [event_view(event, names) for event in feed if event.kind not in hidden],
    }


def chain_view(game: Game, event_id: int) -> dict[str, Any]:
    """An event and its ancestors, for the chain viewer."""
    log = game.sim.log
    if event_id < 0 or event_id >= len(log):
        raise ValueError(f"no event with id {event_id}")
    names = _place_names(game)
    wanted = sorted(ancestors(log, event_id) | {event_id}, reverse=True)[:MAX_CHAIN_NODES]
    return {"event_id": event_id,
            "nodes": [event_view(log.get(i), names) for i in sorted(wanted)]}


def concept_view(content: Content, concept_id: str) -> dict[str, Any] | None:
    """A concept card with its competency and badge, or None if unknown."""
    concept = content.concepts.get(concept_id)
    if concept is None:
        return None
    statuses = [content.parameter_status.get(name, "illustrative")
                for name in concept.get("parameters", [])]
    reviewed = concept.get("status") == "reviewed" and all(s == "reviewed" for s in statuses)
    return {"id": concept_id, "title": concept["title"], "body": concept["body"],
            "badge": "reviewed" if reviewed else "illustrative",
            "competency": dict(content.competencies[concept["competency"]])}


def results_view(content: Content, game: Game, results: Results) -> dict[str, Any]:
    """Score, diff versus baseline and the top cause chains."""
    names = _place_names(game)
    log, baseline_log = game.sim.log, results.baseline.log
    result = results.diff
    chains = []
    for chain in results.chains:
        chains.append({"events": [event_view(log.get(i), names) for i in chain.event_ids],
                       "concept": concept_view(content, chain.concept_id)})
    cases_key = "infectious.cum_cases"
    return {
        "player": result.player.to_dict(), "baseline": result.baseline.to_dict(),
        "deltas": {"cases_averted": result.cases_averted,
                   "deaths_averted": result.deaths_averted,
                   "coverage_gain": round(result.coverage_gain, 4) + 0.0,
                   "gap_reduction": round(result.gap_reduction, 4) + 0.0,
                   "trust_gain": round(result.trust_gain, 4) + 0.0,
                   "stockouts_added": result.stockouts_added},
        "health_score": results.health.to_dict(), "ripple_score": results.ripple.to_dict(),
        "ripple_size": result.ripple_size,
        "added": dict(sorted(Counter(log.get(i).kind for i in result.only_player).items())),
        "prevented": dict(sorted(Counter(baseline_log.get(i).kind
                                         for i in result.only_baseline).items())),
        "chains": chains,
        "series": {"player_cases": game.sim.series.get(cases_key, []),
                   "baseline_cases": results.baseline.series.get(cases_key, [])},
    }
