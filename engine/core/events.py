"""Event log with cause tracking (the signature feature, SDD 4.5).

Contract
- Events get increasing integer ids. An event's causes must all be earlier
  events, so the cause graph is acyclic by construction.
- Only root kinds (the genesis event and player actions) may have no cause.
- `causes` are real mechanisms ("the stock-out cancelled the session").
  `influences` are weaker: earlier events, downstream of a player action, that
  may have changed whether or how this event happened (see ADR-005). The cause
  graph of SDD 4.5 uses `causes` only; influences are kept apart so the chain
  viewer never presents a "may have shifted" link as a cause.
- `roots(id)` gives the player-action events an event descends from through
  causes or influences. An event with a non-empty root set is called
  "tainted": the player may have changed it.
- `digest()` is a stable hash of the whole log, used by determinism tests.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass

GENESIS_KIND = "core.genesis"
ACTION_KIND = "player.action"
ROOT_KINDS = (GENESIS_KIND, ACTION_KIND)
GENESIS_ID = 0

Payload = Mapping[str, int | float | str | bool]


class CauseError(ValueError):
    """Raised when an event breaks the cause rules."""


@dataclass(frozen=True)
class Event:
    """One thing that happened. See SDD 4.5 for the field meanings."""

    id: int
    tick: int
    kind: str
    place_id: str
    payload: Payload
    causes: tuple[int, ...]
    domain: str
    influences: tuple[int, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Plain-dict form for JSON."""
        return {
            "id": self.id,
            "tick": self.tick,
            "kind": self.kind,
            "place_id": self.place_id,
            "payload": dict(sorted(self.payload.items())),
            "causes": list(self.causes),
            "domain": self.domain,
            "influences": list(self.influences),
        }


class EventLog:
    """Append-only list of events plus indexes for graph queries."""

    def __init__(self) -> None:
        self._events: list[Event] = []
        self._children: list[list[int]] = []
        self._influenced: list[list[int]] = []
        self._roots: list[frozenset[int]] = []

    def append(
        self,
        tick: int,
        kind: str,
        place_id: str,
        payload: Payload,
        causes: Sequence[int],
        domain: str,
        influences: Sequence[int] = (),
    ) -> Event:
        """Validate and store a new event; returns it with its id."""
        new_id = len(self._events)
        unique_causes = tuple(sorted(set(causes)))
        if not unique_causes and kind not in ROOT_KINDS:
            raise CauseError(f"event {kind!r} at {place_id} has no cause")
        unique_influences = tuple(sorted(set(influences) - set(unique_causes)))
        for cause in unique_causes + unique_influences:
            if cause < 0 or cause >= new_id:
                raise CauseError(f"event {kind!r} lists cause {cause}, not an earlier event")
        event = Event(new_id, tick, kind, place_id, dict(payload), unique_causes, domain,
                      unique_influences)
        roots: set[int] = {new_id} if kind == ACTION_KIND else set()
        for cause in unique_causes:
            roots |= self._roots[cause]
            self._children[cause].append(new_id)
        for influence in unique_influences:
            roots |= self._roots[influence]
            self._influenced[influence].append(new_id)
        self._events.append(event)
        self._children.append([])
        self._influenced.append([])
        self._roots.append(frozenset(roots))
        return event

    def __len__(self) -> int:
        return len(self._events)

    def __iter__(self) -> Iterator[Event]:
        return iter(self._events)

    def get(self, event_id: int) -> Event:
        """Event by id."""
        return self._events[event_id]

    def children(self, event_id: int) -> tuple[int, ...]:
        """Ids of events that list `event_id` as a cause."""
        return tuple(self._children[event_id])

    def influenced(self, event_id: int) -> tuple[int, ...]:
        """Ids of events that list `event_id` as an influence."""
        return tuple(self._influenced[event_id])

    def roots(self, event_id: int) -> frozenset[int]:
        """Player-action event ids this event descends from (may be empty)."""
        return self._roots[event_id]

    def is_tainted(self, event_id: int) -> bool:
        """True if the event descends from at least one player action."""
        return bool(self._roots[event_id])

    def to_dicts(self) -> list[dict[str, object]]:
        """All events as plain dicts."""
        return [event.to_dict() for event in self._events]

    def digest(self) -> str:
        """SHA-256 of the canonical JSON form of the log."""
        text = json.dumps(self.to_dicts(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
