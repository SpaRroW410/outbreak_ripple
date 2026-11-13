"""The tick pipeline (SDD 4.4): one `Simulation` holds one run in progress.

Order inside `advance()`:
  1. (player action effects were applied by the caller at turn start)
  2-3. scheduled events due now are logged and delivered; each domain steps in
       registry order (the systems domain is registered first, so stock, trust
       and rumours update before disease dynamics)
  4. events are appended to the log by `TickContext.emit`, causes attached
  5. tipping-point follow-ups were queued by domains for a later tick
  6. per-tick metric totals are recorded

Contract: this module knows the `Domain` protocol only, never concrete domains.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from engine.core.clock import Clock
from engine.core.district import District
from engine.core.domain import Domain, Params, TickContext, WorldView
from engine.core.events import GENESIS_KIND, Event, EventLog
from engine.core.ids import DISTRICT_ID
from engine.core.rng import Rng
from engine.core.schedule import Schedule
from engine.core.state import Scalar, StateStore, StateView


@dataclass(frozen=True)
class RunResult:
    """Everything kept from a finished (or paused) run."""

    seed_text: str
    district: District
    log: EventLog
    final_state: dict[str, dict[str, Scalar]]
    series: dict[str, list[float]]  # key -> total over places, one entry per tick
    tainted_cells: frozenset[tuple[str, str]]  # (key, place) possibly changed by the player


class Simulation:
    """One run of the district: state, event log, schedule and clock."""

    def __init__(self, district: District, domains: Sequence[Domain], params: Params,
                 seed_text: str, clock: Clock, noise: int = 0) -> None:
        self.district = district
        self.domains = tuple(domains)
        self.params = params
        self.seed_text = seed_text
        self.clock = clock
        self.tick = 0
        self.state = StateStore()
        self.log = EventLog()
        self.schedule = Schedule()
        self.series: dict[str, list[float]] = {}
        dynamics = Rng(seed_text).fork(f"noise{noise}")
        self._rngs: dict[str, Rng] = {}
        self._views: dict[str, StateView] = {}
        self._check_single_writer()
        self.log.append(0, GENESIS_KIND, DISTRICT_ID, {}, (), "core")
        for domain in self.domains:
            self._rngs[domain.name] = dynamics.fork(domain.name)
            self._views[domain.name] = self.state.view(domain.name, domain.reads, domain.writes)
            world = WorldView(district, self._views[domain.name], params)
            domain.init_state(world, self._rngs[domain.name].fork("init"))

    def _check_single_writer(self) -> None:
        """Each state key has exactly one owning domain."""
        owner: dict[str, str] = {}
        for domain in self.domains:
            for key in sorted(domain.writes):
                if key in owner:
                    raise ValueError(f"{key!r} written by {owner[key]} and {domain.name}")
                owner[key] = domain.name

    @property
    def finished(self) -> bool:
        """True once all ticks of the run have been simulated."""
        return self.tick >= self.clock.ticks_per_run

    def advance(self) -> list[Event]:
        """Simulate one tick; returns the events logged during it."""
        first_new = len(self.log)
        inboxes: dict[str, list[Event]] = {domain.name: [] for domain in self.domains}
        for item in self.schedule.pop_due(self.tick):
            domain_name = item.kind.split(".", 1)[0]
            if domain_name not in inboxes:
                raise ValueError(f"scheduled event {item.kind!r} has no domain to receive it")
            event = self.log.append(self.tick, item.kind, item.place_id, item.payload,
                                    item.causes, domain_name)
            inboxes[domain_name].append(event)
        for domain in self.domains:
            ctx = TickContext(self.tick, self.district, self._views[domain.name],
                              self._rngs[domain.name], self.params,
                              tuple(inboxes[domain.name]), domain.name, self.log, self.schedule)
            returned = domain.step(ctx)
            if [e.id for e in returned] != [e.id for e in ctx.emitted]:
                raise ValueError(f"domain {domain.name} must return exactly the events it emitted")
        for key, total in self.state.totals().items():
            self.series.setdefault(key, []).append(total)
        self.tick += 1
        return [self.log.get(i) for i in range(first_new, len(self.log))]

    def advance_to(self, tick: int) -> None:
        """Simulate until the clock shows `tick` (or the run ends)."""
        while self.tick < tick and not self.finished:
            self.advance()

    def result(self) -> RunResult:
        """Snapshot of the run so far."""
        return RunResult(self.seed_text, self.district, self.log, self.state.snapshot(),
                         {key: list(values) for key, values in self.series.items()},
                         self.state.tainted_cells())
