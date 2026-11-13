"""Conservation (SDD 11): people are neither created nor lost; stock never negative."""

from tests.conftest import write_report
from tools.experiments import pmap
from tools.experiments_ripple import conservation_worker

SEEDS = 200


def test_population_and_stock_invariants_hold_every_tick() -> None:
    rows = pmap(conservation_worker, [f"cons-{i}" for i in range(SEEDS)])
    problems = [problem for row in rows for problem in row["problems"]]
    write_report("conservation", {"seeds": SEEDS, "ticks_checked": sum(r["ticks"] for r in rows),
                                  "violations": len(problems),
                                  "doses_given": sum(r["doses_given"] for r in rows)})
    assert problems == []
    assert sum(row["doses_given"] for row in rows) > 0
