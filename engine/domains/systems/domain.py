"""Systems domain plugin: wires the block and village updates into the contract.

Model summary: docs/models/systems.md. Parameters: content/parameters/systems.json.
"""

from __future__ import annotations

from engine.core.domain import ConceptTrigger, TickContext, WorldView
from engine.core.events import GENESIS_ID, Event
from engine.core.rng import Rng
from engine.domains.systems import keys as k
from engine.domains.systems.blocks import step_block
from engine.domains.systems.villages import step_village

STOCK_ARRIVAL = "systems.stock_arrival"
RUMOUR_SPREAD = "systems.rumour_spread"


class SystemsDomain:
    """Stock, cold chain, trust, rumours and workload."""

    name = "systems"
    reads = k.READS
    writes = k.WRITES

    def init_state(self, world: WorldView, rng: Rng) -> None:
        """Create block and village cells with starting values."""
        params, state = world.params, world.state
        interval = int(params["systems.session_interval_weeks"])
        for block in world.district.blocks:
            population = world.district.block_population(block.id)
            stock = round(population * params["systems.stock_initial_per_1000"] / 1000)
            for key, value in ((k.VACCINE_STOCK, stock), (k.VACCINE_POTENCY, 1.0),
                               (k.STOCK_CAUSE, GENESIS_ID), (k.STOCKED_OUT, 0),
                               (k.COLD_CHAIN_OK, 1), (k.COLD_CHAIN_CARE, 0),
                               (k.COLD_CHAIN_EVENT, GENESIS_ID),
                               (k.WORKLOAD, params["systems.workload_base"]), (k.STAFF, 1.0),
                               (k.MORALE, 0.7), (k.OVERLOADED, 0)):
                state.define(key, block.id, value)
        for index, village in enumerate(world.district.villages):
            village_rng = rng.fork(village.id)
            trust = round(village_rng.uniform(params["systems.trust_initial_min"],
                                              params["systems.trust_initial_max"]), 3)
            rumour = round(village_rng.uniform(0.0, params["systems.rumour_initial_max"]), 3)
            for key, value in ((k.TRUST, trust), (k.TRUST_BASE, trust), (k.TRUST_LOW, 0),
                               (k.RUMOUR, rumour), (k.RUMOUR_HIGH, 0),
                               (k.RUMOUR_CAUSE, GENESIS_ID), (k.SURVEILLANCE, 0.0),
                               (k.SESSION_DOSES, 0), (k.SESSION_OFFSET, index % interval),
                               (k.SESSION_BOOST, 1.0), (k.CAMPAIGN_DOSES, 0),
                               (k.SEEN_OUTBREAK, 0), (k.SEEN_DEATHS, 0)):
                state.define(key, village.id, value)

    def step(self, ctx: TickContext) -> list[Event]:
        """One week: deliveries, then blocks, then villages (sorted order)."""
        for event in ctx.inbox:
            ctx.begin_scope(event.id)
            self._receive(ctx, event)
        for block in ctx.district.blocks:
            ctx.begin_scope()
            step_block(ctx, block)
        for village in ctx.district.villages:
            ctx.begin_scope()
            step_village(ctx, village)
        return ctx.emitted

    def _receive(self, ctx: TickContext, event: Event) -> None:
        """Apply a scheduled event addressed to this domain."""
        state = ctx.state
        if event.kind == STOCK_ARRIVAL:
            doses = int(event.payload["doses"])
            stock = state.count(k.VACCINE_STOCK, event.place_id)
            potency = state.num(k.VACCINE_POTENCY, event.place_id)
            mixed = (stock * potency + doses) / max(1, stock + doses)
            state.set(k.VACCINE_STOCK, event.place_id, stock + doses)
            state.set(k.VACCINE_POTENCY, event.place_id, round(mixed, 4))
            state.set(k.STOCK_CAUSE, event.place_id, event.id)
        elif event.kind == RUMOUR_SPREAD:
            state.add(k.RUMOUR, event.place_id, float(event.payload["amount"]), 0.0, 1.0)
            state.set(k.RUMOUR_CAUSE, event.place_id, event.id)
        else:
            raise ValueError(f"systems domain cannot handle scheduled event {event.kind!r}")

    def concept_triggers(self) -> list[ConceptTrigger]:
        """Event kinds that demonstrate concept cards."""
        return [
            ConceptTrigger("cold_chain", "systems.cold_chain_failure"),
            ConceptTrigger("stock_management", "systems.stockout"),
            ConceptTrigger("stock_management", "systems.session_missed"),
            ConceptTrigger("rumours_and_hesitancy", "systems.rumour_surge"),
            ConceptTrigger("rumours_and_hesitancy", "systems.rumour_spread"),
            ConceptTrigger("aefi_communication", "systems.aefi_rumour"),
            ConceptTrigger("community_trust", "systems.trust_collapse"),
            ConceptTrigger("health_worker_workload", "systems.staff_overload"),
        ]
