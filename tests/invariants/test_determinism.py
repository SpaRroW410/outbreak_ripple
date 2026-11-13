"""Determinism (SDD 11): 200 seeds, each run twice plus a replay; identical logs and hashes."""

from tests.conftest import write_report
from tools.experiments import determinism_worker, pmap

SEEDS = 200


def test_200_seeds_identical_logs_and_states() -> None:
    rows = pmap(determinism_worker, [f"det-{i}" for i in range(SEEDS)])
    mismatched = [row["seed"] for row in rows if len(set(row["digests"])) != 1]
    states_differ = [row["seed"] for row in rows if not row["states_equal"]]
    write_report("determinism", {
        "seeds": SEEDS, "runs_per_seed": 3, "mismatched_seeds": len(mismatched),
        "state_mismatches": len(states_differ),
        "distinct_logs": len({row["digests"][0] for row in rows}),
        "mean_events_per_run": round(sum(row["events"] for row in rows) / SEEDS, 1)})
    assert mismatched == []
    assert states_differ == []
    assert len({row["digests"][0] for row in rows}) == SEEDS  # seeds really differ
