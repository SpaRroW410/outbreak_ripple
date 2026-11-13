"""End-of-run results: baseline comparison, scores and explanations in one place."""

from __future__ import annotations

from dataclasses import dataclass

from engine.content import Content
from engine.core.pipeline import RunResult
from engine.registry import build_domains
from engine.runner import run
from engine.scoring.diff import Diff, diff
from engine.scoring.explain import ChainExplanation, top_chains
from engine.scoring.metrics import outcome
from engine.scoring.score import (
    HealthScore,
    RippleScore,
    public_health_score,
    ripple_score,
    surprise,
)


@dataclass(frozen=True)
class Results:
    """Everything the results screen shows."""

    baseline: RunResult
    diff: Diff
    health: HealthScore
    ripple: RippleScore
    chains: list[ChainExplanation]


def compute_results(content: Content, player: RunResult, baseline: RunResult | None = None,
                    with_surprise: bool = True) -> Results:
    """Run the baseline (and noise runs for surprise) and score the player's run."""
    scoring = content.theme["scoring"]
    if baseline is None:
        baseline = run(content, player.seed_text, [])
    result = diff(player, baseline)
    noise_cases = [result.baseline.cases]
    if with_surprise and result.ripple_size > 0:
        for noise in range(1, int(scoring["surprise_noise_runs"]) + 1):
            noise_cases.append(outcome(run(content, player.seed_text, [], noise)).cases)
    surprise_value = surprise(result.player.cases, noise_cases) if len(noise_cases) > 1 else 0.0
    triggers = [trigger for domain in build_domains() for trigger in domain.concept_triggers()]
    card_concepts = {card.id: card.concepts for card in content.cards.values()}
    chains = top_chains(player, result, triggers, scoring["chain_event_weights"], card_concepts)
    return Results(baseline, result, public_health_score(result, scoring),
                   ripple_score(player, result, surprise_value), chains)
