"""The domain plugin contract (SDD section 5).

A domain is one package in `engine/domains/<name>/` exposing a class that
satisfies `Domain`. Domains never import each other; they share information
only through declared state keys.

`init_state(world, rng)`: `world` is a `WorldView` (the static district, the
domain's state view and the parameters) because `init_state` returns nothing
and needs somewhere to write (ADR-003).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from engine.core.district import District
from engine.core.events import GENESIS_ID, Event, EventLog, Payload
from engine.core.rng import Rng
from engine.core.schedule import Schedule, ScheduledEvent
from engine.core.state import StateView

Params = Mapping[str, float]


@dataclass(frozen=True)
class ConceptTrigger:
    """Events of `event_kind` demonstrate the concept card `concept_id`."""

    concept_id: str
    event_kind: str


@dataclass
class WorldView:
    """What a domain sees when it sets up its state."""

    district: District
    state: StateView
    params: Params


@dataclass
class TickContext:
    """Everything a domain may use during one tick."""

    tick: int
    district: District
    state: StateView
    rng: Rng  # the domain's own stream; fork it per place and tick
    params: Params
    inbox: tuple[Event, ...]  # scheduled events delivered to this domain now
    domain: str
    log: EventLog
    schedule_queue: Schedule
    emitted: list[Event] = field(default_factory=list)
    genesis_id: int = GENESIS_ID

    def begin_scope(self, *cause_ids: int) -> None:
        """Start work on one place. Pass ids of events that triggered the work."""
        tainted = [cause for cause in cause_ids if self.log.is_tainted(cause)]
        self.state.begin_scope(max(tainted) if tainted else None)

    def emit(self, kind: str, place_id: str, payload: Payload, causes: Sequence[int]) -> Event:
        """Append an event caused by `causes` (at least one is required)."""
        if not kind.startswith(self.domain + "."):
            raise ValueError(f"domain {self.domain!r} cannot emit {kind!r}")
        event = self.log.append(self.tick, kind, place_id, payload, causes, self.domain,
                                self._influences(causes))
        if self.log.is_tainted(event.id):
            self.state.mark(event.id)
        self.emitted.append(event)
        return event

    def schedule(self, delay: int, kind: str, place_id: str, payload: Payload,
                 causes: Sequence[int]) -> None:
        """Queue a follow-up event `delay` ticks from now (delay >= 1)."""
        if delay < 1:
            raise ValueError("follow-up events must be scheduled for a later tick")
        item = ScheduledEvent(self.tick + delay, kind, place_id, dict(payload),
                              tuple(causes), tuple(self._influences(causes)))
        self.schedule_queue.add(item)

    def _influences(self, causes: Sequence[int]) -> list[int]:
        """The scope taint as an influence, unless a real cause is already tainted."""
        taint = self.state.scope_taint
        if taint is None or any(self.log.is_tainted(cause) for cause in causes):
            return []
        return [taint]


class Domain(Protocol):
    """Interface every domain implements. See SDD section 5."""

    name: str
    reads: frozenset[str]
    writes: frozenset[str]

    def init_state(self, world: WorldView, rng: Rng) -> None:
        """Create this domain's state cells."""
        ...

    def step(self, ctx: TickContext) -> list[Event]:
        """Advance one tick and return the events emitted."""
        ...

    def concept_triggers(self) -> list[ConceptTrigger]:
        """Which event kinds demonstrate which concept cards."""
        ...
