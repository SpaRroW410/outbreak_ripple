"""Scores and golden run."""

import json

from engine.content import Content
from engine.core.graph import ancestors
from engine.results import compute_results
from engine.runner import run
from engine.scoring.diff import diff
from engine.scoring.score import surprise
from tools.update_golden import GOLDEN_FILE, PLAYS, SEED, compute


def test_golden_run_matches_stored_hash() -> None:
    """If this fails after an intended behaviour change: python -m tools.update_golden + NEWS."""
    stored = json.loads(GOLDEN_FILE.read_text(encoding="utf-8"))
    assert compute() == stored


def test_no_actions_scores_zero(content: Content) -> None:
    baseline = run(content, "zero", [])
    results = compute_results(content, run(content, "zero", []), baseline)
    assert results.diff.is_zero
    assert results.health.total == 0 and results.ripple.total == 0 and results.chains == []


def test_scores_and_chains_for_the_golden_plays(content: Content) -> None:
    player, baseline = run(content, SEED, PLAYS), run(content, SEED, [])
    results = compute_results(content, player, baseline)
    assert not diff(player, baseline).is_zero
    weights = content.theme["scoring"]
    limit = sum(weights[key] for key in ("weight_deaths", "weight_cases", "weight_coverage",
                                         "weight_equity"))
    assert -limit <= results.health.total <= limit
    assert results.ripple.reach > 0 and results.ripple.depth >= 2
    assert 0.0 <= results.ripple.surprise <= 1.0
    assert 1 <= len(results.chains) <= 3
    for chain in results.chains:
        ids = chain.event_ids
        assert player.log.get(ids[0]).kind == "player.action"
        assert all(ids[i] in ancestors(player.log, ids[i + 1], wide=True)
                   for i in range(len(ids) - 1))
        assert all(i in results.diff.only_player for i in ids[1:])
        assert chain.concept_id in content.concepts


def test_surprise_is_high_only_for_unusual_outcomes() -> None:
    noise = [100, 110, 90, 105, 95, 100]
    assert surprise(100, noise) == 0.0
    assert surprise(500, noise) == 1.0
    assert surprise(100, []) == 0.0
