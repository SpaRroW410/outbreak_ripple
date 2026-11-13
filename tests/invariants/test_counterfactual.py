"""Counterfactual (SDD 11): empty actions give zero diff; one card differs only downstream."""

from tests.conftest import write_report
from tools.experiments import pmap
from tools.experiments_ripple import counterfactual_worker

SEEDS = 200


def test_empty_is_zero_and_single_card_differs_only_downstream() -> None:
    rows = pmap(counterfactual_worker, [f"cf-{i}" for i in range(SEEDS)])
    report = {
        "seeds": SEEDS,
        "empty_diff_nonzero": sum(1 for row in rows if not row["empty_diff_is_zero"]),
        "runs_with_any_difference": sum(1 for row in rows if row["ripple_size"] > 0),
        "player_only_events": sum(row["only_player"] for row in rows),
        "player_only_events_not_downstream": sum(row["untainted_player_only"] for row in rows),
        "differences_before_action": sum(row["differences_before_action"] for row in rows),
        "changed_state_cells": sum(row["changed_cells"] for row in rows),
        "changed_state_cells_without_taint": sum(row["changed_cells_without_taint"]
                                                 for row in rows),
    }
    write_report("counterfactual", report)
    assert report["empty_diff_nonzero"] == 0
    assert report["player_only_events_not_downstream"] == 0
    assert report["differences_before_action"] == 0
    assert report["changed_state_cells_without_taint"] == 0
    assert report["runs_with_any_difference"] > SEEDS // 4  # the test is not vacuous
