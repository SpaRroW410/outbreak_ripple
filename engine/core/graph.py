"""Cause-graph utilities over an EventLog (SDD 4.5).

Contract: read-only functions. Because causes always have lower ids, a single
pass in id order is a topological order; no recursion is needed.
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.core.events import EventLog


@dataclass(frozen=True)
class BlastRadius:
    """What a player action touched: places, population groups, domains."""

    event_count: int
    places: tuple[str, ...]
    groups: tuple[str, ...]
    domains: tuple[str, ...]


def ancestors(log: EventLog, event_id: int) -> set[int]:
    """All events that `event_id` descends from (not including itself)."""
    found: set[int] = set()
    stack = list(log.get(event_id).causes)
    while stack:
        current = stack.pop()
        if current not in found:
            found.add(current)
            stack.extend(log.get(current).causes)
    return found


def descendants(log: EventLog, event_id: int) -> set[int]:
    """All events caused, directly or indirectly, by `event_id`."""
    found: set[int] = set()
    stack = list(log.children(event_id))
    while stack:
        current = stack.pop()
        if current not in found:
            found.add(current)
            stack.extend(log.children(current))
    return found


def longest_chain(log: EventLog, from_id: int) -> list[int]:
    """Longest cause path starting at `from_id`, as a list of event ids.

    Ties are broken towards the lowest event id so the result is deterministic.
    """
    reachable = descendants(log, from_id) | {from_id}
    best_length: dict[int, int] = {from_id: 1}
    best_parent: dict[int, int] = {}
    for current in sorted(reachable):
        if current == from_id:
            continue
        for cause in log.get(current).causes:
            if cause in best_length and best_length[cause] + 1 > best_length.get(current, 0):
                best_length[current] = best_length[cause] + 1
                best_parent[current] = cause
    end = min(best_length, key=lambda event_id: (-best_length[event_id], event_id))
    return chain_to(best_parent, from_id, end)


def chain_to(parents: dict[int, int], from_id: int, end_id: int) -> list[int]:
    """Follow `parents` back from `end_id` to `from_id`; returns ids in time order."""
    chain = [end_id]
    while chain[-1] != from_id:
        chain.append(parents[chain[-1]])
    chain.reverse()
    return chain


def longest_chain_to(log: EventLog, from_id: int, end_id: int) -> list[int]:
    """Longest cause path from `from_id` to `end_id` ([] if not connected)."""
    between = (ancestors(log, end_id) | {end_id}) & (descendants(log, from_id) | {from_id})
    if from_id not in between or end_id not in between:
        return []
    best_length: dict[int, int] = {from_id: 1}
    best_parent: dict[int, int] = {}
    for current in sorted(between):
        for cause in log.get(current).causes:
            if cause in best_length and best_length[cause] + 1 > best_length.get(current, 0):
                best_length[current] = best_length[cause] + 1
                best_parent[current] = cause
    return chain_to(best_parent, from_id, end_id)


def blast_radius(log: EventLog, action_id: int) -> BlastRadius:
    """Places, groups and domains touched downstream of a player action."""
    touched = descendants(log, action_id)
    places: set[str] = set()
    groups: set[str] = set()
    domains: set[str] = set()
    for event_id in touched:
        event = log.get(event_id)
        places.add(event.place_id)
        domains.add(event.domain)
        group = event.payload.get("group")
        if isinstance(group, str):
            groups.add(group)
    return BlastRadius(len(touched), tuple(sorted(places)), tuple(sorted(groups)),
                       tuple(sorted(domains)))
