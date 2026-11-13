"""Game rules, the JSON API and the session export."""

import json
from typing import Any

import pytest

from engine.api import Session
from engine.content import Content
from engine.game import Game, InvalidPlayError
from engine.runner import run
from tools.content_io import load_bundle
from tools.experiments import random_game


def first_target(state: dict[str, Any], card: dict[str, Any]) -> str:
    block = state["district"]["blocks"][0]
    return {"village": block["villages"][0]["id"], "block": block["id"],
            "district": "D"}[card["target_kind"]]


def test_turn_rules(content: Content) -> None:
    game = Game(content, "rules")
    hand = game.hand()
    assert len(hand) == 5
    cheap = sorted(hand, key=lambda card: card.budget_cost)
    with pytest.raises(InvalidPlayError):
        game.check([(card.id, game.targets(card)[0]) for card in cheap[:3]])  # too many cards
    with pytest.raises(InvalidPlayError):
        game.check([("not_a_card", "D")])
    with pytest.raises(InvalidPlayError):
        game.check([(cheap[0].id, "nowhere")])
    game.budget = 0
    costly = [card for card in hand if card.budget_cost > 0][0]
    with pytest.raises(InvalidPlayError):
        game.check([(costly.id, game.targets(costly)[0])])


def test_game_equals_replay(content: Content) -> None:
    game = random_game(content, "replay", "x")
    assert game.finished and game.sim.tick == 52
    assert run(content, "replay", game.plays).log.digest() == game.sim.log.digest()


def test_api_full_loop_and_export() -> None:
    session = Session(load_bundle())
    assert json.loads(session.handle_json('{"cmd": "get_state"}'))["ok"] is False
    state = session.handle("new_game", {"seed": "api"})
    assert state["turn"] == 0 and len(state["hand"]) == 5 and state["feed"] == []
    assert json.loads(session.handle_json('{"cmd": "get_diff"}'))["ok"] is False  # not finished
    hidden = set(session.content.theme["feed_hidden_kinds"])
    while not state["finished"]:
        card = min(state["hand"], key=lambda c: c["budget_cost"])
        request = {"cmd": "play_turn", "args": {"plays": [
            {"card_id": card["id"], "target": first_target(state, card)}]}}
        reply = json.loads(session.handle_json(json.dumps(request)))
        assert reply["ok"], reply
        state = reply["result"]
        assert not hidden & {event["kind"] for event in state["feed"]}
    assert state["turn"] == 6 and state["hand"] == []
    results = session.handle("get_diff", {})
    assert set(results) >= {"player", "baseline", "deltas", "health_score", "ripple_score",
                            "ripple_size", "chains", "prevented", "added", "series"}
    assert len(results["series"]["player_cases"]) == 52
    for chain in results["chains"]:
        assert chain["events"][0]["kind"] == "player.action"
        if chain["concept"] is not None:
            assert chain["concept"]["badge"] == "illustrative"
            assert chain["concept"]["competency"]["verified"] is False
    last = state["feed"][-1]["id"]
    chain = session.handle("get_chain", {"event_id": last})
    assert chain["nodes"][-1]["id"] == last and chain["nodes"][0]["id"] < last
    export = session.handle("export_session", {"concepts_viewed": ["herd_immunity"]})
    assert set(export) == {"schema_version", "engine_version", "content_version", "seed",
                           "plays", "scores", "counters"}
    assert len(export["plays"]) == 6 and sum(export["counters"]["cards_by_family"].values()) == 6
    json.dumps(export)  # serialisable


def test_every_event_kind_has_english_text(content: Content) -> None:
    strings = load_bundle()["i18n"]["en"]
    kinds: set[str] = set()
    for seed in range(12):
        kinds |= {event.kind for event in random_game(content, f"kinds-{seed}", "k").sim.log}
    missing = sorted(kind for kind in kinds if f"event.{kind}" not in strings)
    assert missing == []
