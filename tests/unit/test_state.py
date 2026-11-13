"""State store: declared reads/writes are enforced; taint follows information flow."""

import pytest

from engine.core.state import StateStore, UndeclaredAccessError


def make_store() -> StateStore:
    store = StateStore()
    owner = store.view("a", [], ["a.x", "a.y"])
    owner.define("a.x", "P1", 1)
    owner.define("a.x", "P2", 2)
    owner.define("a.y", "P1", 0.5)
    return store


def test_undeclared_write_raises() -> None:
    store = make_store()
    reader = store.view("b", ["a.x"], [])
    assert reader.get("a.x", "P1") == 1
    with pytest.raises(UndeclaredAccessError):
        reader.set("a.x", "P1", 5)


def test_undeclared_read_raises() -> None:
    store = make_store()
    stranger = store.view("c", [], [])
    with pytest.raises(UndeclaredAccessError):
        stranger.get("a.x", "P1")
    with pytest.raises(UndeclaredAccessError):
        stranger.get_or("a.x", "P1", 0)


def test_get_or_default_for_missing_cell() -> None:
    view = make_store().view("b", ["other.key"], [])
    assert view.get_or("other.key", "P1", 7) == 7


def test_add_clamps_and_keeps_ints() -> None:
    store = make_store()
    view = store.view("a", [], ["a.x", "a.y"])
    view.add("a.x", "P1", 2)
    assert store.peek("a.x", "P1") == 3 and isinstance(store.peek("a.x", "P1"), int)
    view.add("a.y", "P1", 0.9, 0.0, 1.0)
    assert store.peek("a.y", "P1") == 1.0


def test_player_view_rejects_unknown_keys() -> None:
    player = make_store().player_view()
    with pytest.raises(KeyError):
        player.set("no.such", "P1", 1)


def test_taint_spreads_through_reads_and_clears_on_clean_write() -> None:
    store = make_store()
    player = store.player_view()
    player.begin_scope(42)
    player.set("a.x", "P1", 9)
    assert ("a.x", "P1") in store.tainted_cells()
    view = store.view("a", [], ["a.x", "a.y"])
    view.begin_scope()
    view.set("a.y", "P1", view.count("a.x", "P1") / 10)  # read tainted, then write
    assert ("a.y", "P1") in store.tainted_cells()
    view.begin_scope()
    view.set("a.y", "P1", 0.0)  # nothing tainted was read in this scope
    assert ("a.y", "P1") not in store.tainted_cells()


def test_snapshot_is_a_copy_and_totals_sum() -> None:
    store = make_store()
    snapshot = store.snapshot()
    snapshot["a.x"]["P1"] = 100
    assert store.peek("a.x", "P1") == 1
    assert store.totals()["a.x"] == 3.0
