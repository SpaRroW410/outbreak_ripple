"""Future events waiting for their tick (delayed card effects, tipping points).

Contract: items are delivered in the order they were scheduled. Delivery turns
an item into a normal event in the log; the pipeline hands it to the domain
named by the event kind's prefix (the text before the first dot).
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.core.events import Payload


@dataclass(frozen=True)
class ScheduledEvent:
    """An event that will be appended to the log at `due_tick`."""

    due_tick: int
    kind: str
    place_id: str
    payload: Payload
    causes: tuple[int, ...]


class Schedule:
    """Ordered list of pending events."""

    def __init__(self) -> None:
        self._pending: list[ScheduledEvent] = []

    def add(self, item: ScheduledEvent) -> None:
        """Queue an item."""
        self._pending.append(item)

    def pop_due(self, tick: int) -> list[ScheduledEvent]:
        """Remove and return items due at or before `tick`, in scheduling order."""
        due = [item for item in self._pending if item.due_tick <= tick]
        self._pending = [item for item in self._pending if item.due_tick > tick]
        return due

    def __len__(self) -> int:
        return len(self._pending)
