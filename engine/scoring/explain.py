"""Explain screen data: the top cause chains, one concept card each (SDD section 7)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from engine.core.domain import ConceptTrigger
from engine.core.graph import longest_chain_to
from engine.core.pipeline import RunResult
from engine.scoring.diff import Diff


@dataclass(frozen=True)
class ChainExplanation:
    """A cause chain from a player action to an event only the player's run has."""

    event_ids: tuple[int, ...]  # first is the action, last is the outcome
    concept_id: str  # "" if no concept card matches


def _concept_for(player: RunResult, chain: Sequence[int], triggers: Sequence[ConceptTrigger],
                 card_concepts: Mapping[str, Sequence[str]]) -> str:
    """Concept shown with a chain: latest event with a trigger, else the card's first concept."""
    by_kind = {trigger.event_kind: trigger.concept_id for trigger in triggers}
    for event_id in reversed(chain):
        kind = player.log.get(event_id).kind
        if kind in by_kind:
            return by_kind[kind]
    card_id = str(player.log.get(chain[0]).payload.get("card", ""))
    concepts = card_concepts.get(card_id, ())
    return concepts[0] if concepts else ""


def top_chains(player: RunResult, result: Diff, triggers: Sequence[ConceptTrigger],
               kind_weights: Mapping[str, float], card_concepts: Mapping[str, Sequence[str]],
               limit: int = 3) -> list[ChainExplanation]:
    """Pick up to `limit` chains ending at the weightiest player-only events.

    Chains are chosen greedily by event weight; an outcome already covered by a
    chosen chain, or of a kind already shown at the same place, is skipped.
    """
    candidates = [player.log.get(event_id) for event_id in result.only_player
                  if player.log.is_tainted(event_id)]
    candidates.sort(key=lambda event: (-kind_weights.get(event.kind, 1.0), event.id))
    # Fallback when the player mostly prevented things: other events downstream of an action.
    player_only = set(result.only_player)
    others = [event for event in player.log if player.log.is_tainted(event.id)
              and event.id not in player_only and event.kind in kind_weights]
    others.sort(key=lambda event: (-kind_weights[event.kind], event.id))
    candidates.extend(others)
    chosen: list[ChainExplanation] = []
    covered: set[int] = set()
    seen_kinds: set[str] = set()
    for event in candidates:
        if len(chosen) == limit:
            break
        if event.id in covered or event.kind in seen_kinds:
            continue
        root = min(player.log.roots(event.id))
        chain = longest_chain_to(player.log, root, event.id)
        if len(chain) < 2:
            continue
        concept = _concept_for(player, chain, triggers, card_concepts)
        chosen.append(ChainExplanation(tuple(chain), concept))
        covered.update(chain)
        seen_kinds.add(event.kind)
    return chosen
