"""Infectious domain plugin: wires the village model into the contract.

Model summary: docs/models/infectious.md. Parameters: content/parameters/infectious.json.
"""

from __future__ import annotations

from engine.core.domain import ConceptTrigger, TickContext, WorldView
from engine.core.events import GENESIS_ID, Event
from engine.core.rng import Rng
from engine.domains.infectious import keys as k
from engine.domains.infectious.model import make_rates
from engine.domains.infectious.spread import export_travellers
from engine.domains.infectious.village import step_village

SCHOOL_REOPENS = "infectious.school_reopens"


class InfectiousDomain:
    """Stochastic SEIR-type dynamics per village with vaccination and reporting."""

    name = "infectious"
    reads = k.READS
    writes = k.WRITES

    def init_state(self, world: WorldView, rng: Rng) -> None:
        """Create compartments; choose where and when the index cases appear."""
        params, state = world.params, world.state
        rates = make_rates(params)
        villages = world.district.villages
        seed_rng = rng.fork("index")
        count = min(len(villages), int(params["infectious.index_villages"]))
        seeded = sorted(seed_rng.sample([village.id for village in villages], count))
        seed_ticks = {vid: seed_rng.randint(int(params["infectious.index_tick_min"]),
                                            int(params["infectious.index_tick_max"]))
                      for vid in seeded}
        for village in villages:
            coverage = rng.fork(village.id).uniform(params["infectious.initial_coverage_min"],
                                                    params["infectious.initial_coverage_max"])
            vaccinated = round(village.population * coverage)
            immune = round(vaccinated * params["infectious.vaccine_efficacy"])
            protected = 1 if immune >= rates.herd_threshold * village.population else 0
            for key in k.ALL_KEYS:
                state.define(key, village.id, 0)
            state.set(k.S, village.id, village.population - immune)
            state.set(k.VI, village.id, immune)
            state.set(k.VACCINATED, village.id, vaccinated)
            state.set(k.PROTECTED, village.id, protected)
            state.set(k.LAST_EVENT, village.id, GENESIS_ID)
            state.set(k.INCOMING_CAUSE, village.id, GENESIS_ID)
            state.set(k.SEED_TICK, village.id, seed_ticks.get(village.id, -1))
            state.set(k.TRACING, village.id, 0.0)
            state.set(k.CONTACT_MULT, village.id, 1.0)

    def step(self, ctx: TickContext) -> list[Event]:
        """One week: deliveries, village dynamics, then travel between villages."""
        rates = make_rates(ctx.params)
        for event in ctx.inbox:
            ctx.begin_scope(event.id)
            if event.kind != SCHOOL_REOPENS:
                raise ValueError(f"infectious domain cannot handle {event.kind!r}")
            ctx.state.set(k.CONTACT_MULT, event.place_id, 1.0)
        for village in ctx.district.villages:
            ctx.begin_scope()
            step_village(ctx, village, rates)
        for village in ctx.district.villages:
            ctx.begin_scope()
            export_travellers(ctx, village)
        return ctx.emitted

    def concept_triggers(self) -> list[ConceptTrigger]:
        """Event kinds that demonstrate concept cards."""
        return [
            ConceptTrigger("herd_immunity", "infectious.herd_threshold_reached"),
            ConceptTrigger("importation_and_spread", "infectious.importation"),
            ConceptTrigger("index_case", "infectious.index_case"),
            ConceptTrigger("reporting_delay", "infectious.first_report"),
            ConceptTrigger("outbreak_threshold", "infectious.outbreak_declared"),
            ConceptTrigger("case_fatality", "infectious.death_milestone"),
            ConceptTrigger("epidemic_curve", "infectious.outbreak_over"),
        ]
