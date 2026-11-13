"""Causality (SDD 11): causes exist, the graph is acyclic, longest chain matches brute force."""

from collections.abc import Sequence

from engine.core.events import ROOT_KINDS, EventLog
from engine.core.graph import ancestors, descendants, longest_chain
from tests.conftest import write_report
from tools.experiments import played_result, pmap

SEEDS = 200
SMALL_SEEDS = 40


def check_log(seed_text: str) -> dict[str, int]:
    """Count rule violations in the log of one random game."""
    log = played_result(seed_text).log
    missing = sum(1 for e in log if not e.causes and e.kind not in ROOT_KINDS)
    not_earlier = sum(1 for e in log for cause in e.causes + e.influences if cause >= e.id)
    ticks_backwards = sum(1 for e in log for cause in e.causes if log.get(cause).tick > e.tick)
    return {"events": len(log), "missing_cause": missing, "cause_not_earlier": not_earlier,
            "cause_from_the_future": ticks_backwards}


def brute_force_longest(log: EventLog, start: int) -> int:
    """Length of the longest path from `start`, by trying every path."""
    return 1 + max((brute_force_longest(log, child) for child in log.children(start)), default=0)


def is_real_chain(log: EventLog, chain: Sequence[int]) -> bool:
    return all(chain[i] in log.get(chain[i + 1]).causes for i in range(len(chain) - 1))


def test_every_event_has_an_earlier_cause() -> None:
    rows = pmap(check_log, [f"cause-{i}" for i in range(SEEDS)])
    totals = {key: sum(row[key] for row in rows) for key in rows[0]}
    write_report("causality", {"seeds": SEEDS, **totals})
    assert totals["missing_cause"] == 0
    assert totals["cause_not_earlier"] == 0  # ids only point backwards, so no cycles
    assert totals["cause_from_the_future"] == 0


def test_longest_chain_and_taint_match_brute_force_on_small_worlds() -> None:
    chains_checked = 0
    longest_seen = 0
    for i in range(SMALL_SEEDS):
        log = played_result(f"small-{i}", small=True).log
        actions = [e.id for e in log if e.kind == "player.action"]
        for start in [0, *actions]:
            chain = longest_chain(log, start)
            assert chain[0] == start and is_real_chain(log, chain)
            assert len(chain) == brute_force_longest(log, start)
            chains_checked += 1
            longest_seen = max(longest_seen, len(chain))
        for event in log:
            has_action_ancestor = event.kind == "player.action" or any(
                log.get(a).kind == "player.action" for a in ancestors(log, event.id, wide=True))
            assert log.is_tainted(event.id) == has_action_ancestor
        for action in actions:
            assert all(action in ancestors(log, d) for d in descendants(log, action))
    write_report("causality_brute_force", {"small_worlds": SMALL_SEEDS,
                                           "chains_checked": chains_checked,
                                           "longest_chain_seen": longest_seen, "mismatches": 0})
