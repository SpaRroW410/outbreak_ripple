"""Action cards: effect ops, handlers, taint of everything a card touches."""

import pytest

from engine.actions.apply import apply_card, valid_targets
from engine.actions.ops import resolve_places
from engine.content import Content
from engine.core.events import ACTION_KIND
from engine.runner import build_simulation


def test_resolve_places(small_content: Content) -> None:
    district = build_simulation(small_content, "places").district
    assert resolve_places(district, "B01V02", "target") == ["B01V02"]
    assert resolve_places(district, "B01", "villages") == ["B01V01", "B01V02", "B01V03"]
    assert resolve_places(district, "D", "villages") == [v.id for v in district.villages]
    assert resolve_places(district, "B01V02", "block") == ["B01"]
    assert resolve_places(district, "B02V01", "neighbours") == list(
        district.village("B02V01").neighbours)
    assert resolve_places(district, "D", "blocks") == ["B01", "B02"]
    with pytest.raises(ValueError):
        resolve_places(district, "D", "everywhere")


def test_every_card_applies_and_taints_what_it_changes(small_content: Content) -> None:
    for card in small_content.cards.values():
        for tick in (0, 10):
            sim = build_simulation(small_content, f"card-{card.id}")
            sim.advance_to(tick)
            before = sim.state.snapshot()
            target = valid_targets(sim, card)[0]
            action = apply_card(sim, card, target)
            assert action.kind == ACTION_KIND and action.payload["card"] == card.id
            after = sim.state.snapshot()
            tainted = sim.state.tainted_cells()
            for key, cells in after.items():
                for place, value in cells.items():
                    if before[key][place] != value:
                        assert (key, place) in tainted, f"{card.id}: {key}[{place}] untainted"
            for event in list(sim.log)[action.id + 1:]:
                assert sim.log.roots(event.id) == frozenset({action.id})
            sim.advance_to(sim.clock.ticks_per_run)  # delayed effects are delivered


def test_declarative_card_changes_the_expected_cells(small_content: Content) -> None:
    sim = build_simulation(small_content, "meeting")
    trust = float(sim.state.peek("systems.trust", "B01V01"))
    apply_card(sim, small_content.cards["community_meeting"], "B01V01")
    assert float(sim.state.peek("systems.trust", "B01V01")) == pytest.approx(min(1, trust + 0.1))
    assert float(sim.state.peek("systems.trust", "B01V02")) == sim.state.snapshot()[
        "systems.trust_base"]["B01V02"]


def test_redirect_stock_conserves_doses(small_content: Content) -> None:
    sim = build_simulation(small_content, "redirect")
    total = sim.state.totals()["systems.vaccine_stock"]
    apply_card(sim, small_content.cards["redirect_stock"], "B01")
    assert sim.state.totals()["systems.vaccine_stock"] == total
    assert int(sim.state.peek("systems.vaccine_stock", "B01")) >= 0


def test_emergency_indent_arrives_two_weeks_later(small_content: Content) -> None:
    sim = build_simulation(small_content, "indent")
    apply_card(sim, small_content.cards["emergency_vaccine_indent"], "B02")
    sim.advance_to(3)
    arrivals = [e for e in sim.log if e.kind == "systems.stock_arrival"]
    assert [(e.tick, e.place_id, e.payload["doses"]) for e in arrivals] == [(2, "B02", 600)]
    assert sim.log.is_tainted(arrivals[0].id)
