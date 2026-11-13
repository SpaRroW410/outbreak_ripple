"""Event log rules and cause-graph utilities."""

import pytest

from engine.core.events import ACTION_KIND, GENESIS_KIND, CauseError, EventLog
from engine.core.graph import ancestors, blast_radius, descendants, longest_chain, longest_chain_to


def sample_log() -> EventLog:
    """0 genesis; 1 action; 2<-0; 3<-1; 4<-3; 5<-[2,4]; 6<-1."""
    log = EventLog()
    log.append(0, GENESIS_KIND, "D", {}, [], "core")
    log.append(0, ACTION_KIND, "V1", {"card": "x"}, [], "player")
    log.append(1, "a.one", "V1", {}, [0], "a")
    log.append(1, "a.two", "V1", {}, [1], "a")
    log.append(2, "b.three", "V2", {"group": "under5"}, [3], "b")
    log.append(3, "a.four", "V3", {}, [2, 4], "a")
    log.append(3, "a.five", "V1", {}, [1], "a")
    return log


def test_non_root_event_needs_a_cause() -> None:
    log = sample_log()
    with pytest.raises(CauseError):
        log.append(4, "a.orphan", "V1", {}, [], "a")


def test_cause_must_be_an_earlier_event() -> None:
    log = sample_log()
    with pytest.raises(CauseError):
        log.append(4, "a.future", "V1", {}, [7], "a")


def test_roots_and_taint() -> None:
    log = sample_log()
    assert log.roots(2) == frozenset()
    assert log.roots(5) == frozenset({1})
    assert log.is_tainted(4) and not log.is_tainted(2)


def test_ancestors_and_descendants() -> None:
    log = sample_log()
    assert ancestors(log, 5) == {0, 1, 2, 3, 4}
    assert descendants(log, 1) == {3, 4, 5, 6}
    assert descendants(log, 6) == set()


def test_longest_chain() -> None:
    log = sample_log()
    assert longest_chain(log, 1) == [1, 3, 4, 5]
    assert longest_chain(log, 6) == [6]
    assert longest_chain_to(log, 1, 6) == [1, 6]
    assert longest_chain_to(log, 2, 6) == []


def test_blast_radius() -> None:
    radius = blast_radius(sample_log(), 1)
    assert radius.event_count == 4
    assert radius.places == ("V1", "V2", "V3")
    assert radius.domains == ("a", "b")
    assert radius.groups == ("under5",)


def test_influences_are_kept_apart_from_causes() -> None:
    log = sample_log()
    event = log.append(4, "a.six", "V4", {}, [0], "a", influences=[6])
    assert event.causes == (0,) and event.influences == (6,)
    assert log.is_tainted(event.id)  # downstream of the action through the influence
    assert event.id not in descendants(log, 1)  # ...but not caused by it
    assert event.id in descendants(log, 1, wide=True)
    assert ancestors(log, event.id) == {0}
    assert ancestors(log, event.id, wide=True) == {0, 1, 6}
    assert longest_chain_to(log, 1, event.id) == []
    assert longest_chain_to(log, 1, event.id, wide=True) == [1, 6, event.id]
    assert "V4" in blast_radius(log, 1).places


def test_digest_changes_with_content() -> None:
    first, second = sample_log(), sample_log()
    assert first.digest() == second.digest()
    second.append(5, "a.extra", "V1", {}, [0], "a")
    assert first.digest() != second.digest()
