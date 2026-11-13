"""Stream isolation (SDD 11): adding or removing a domain leaves other domains' draws alone."""

from engine.content import Content
from engine.core.domain import ConceptTrigger, Domain, TickContext, WorldView
from engine.core.events import Event
from engine.core.pipeline import Simulation
from engine.core.rng import Rng
from engine.domains.infectious import InfectiousDomain
from engine.domains.systems import SystemsDomain
from engine.runner import make_clock
from engine.world.generator import generate_district
from tests.conftest import write_report

SEEDS = 20
ID_KEY_ENDINGS = ("_event", "_cause", "seen_outbreak")


class NoisyDomain:
    """A test-only domain that draws many random numbers and emits events every tick."""

    name = "noisy"
    reads: frozenset[str] = frozenset()
    writes = frozenset({"noisy.value"})

    def init_state(self, world: WorldView, rng: Rng) -> None:
        for village in world.district.villages:
            world.state.define("noisy.value", village.id, rng.random())

    def step(self, ctx: TickContext) -> list[Event]:
        for village in ctx.district.villages:
            ctx.begin_scope()
            draws = [ctx.rng.random() for _ in range(7)]
            ctx.state.set("noisy.value", village.id, sum(draws))
            if draws[0] < 0.2:
                ctx.emit("noisy.blip", village.id, {}, [ctx.genesis_id])
        return ctx.emitted

    def concept_triggers(self) -> list[ConceptTrigger]:
        return []


def simulate(content: Content, seed: str, domains: list[Domain]) -> Simulation:
    district = generate_district(Rng(seed).fork("world"), content.theme["world"], content.params)
    sim = Simulation(district, domains, content.params, seed, make_clock(content))
    sim.advance_to(sim.clock.ticks_per_run)
    return sim


def visible(sim: Simulation, domains: set[str]) -> list[tuple[int, str, str, str]]:
    """Events of the given domains without ids (ids shift when another domain emits)."""
    return [(e.tick, e.kind, e.place_id, repr(sorted(e.payload.items())))
            for e in sim.log if e.domain in domains]


def state_of(sim: Simulation, prefixes: tuple[str, ...]) -> dict[str, dict[str, object]]:
    """State of some domains, leaving out cells that hold event ids (ids shift, see above)."""
    return {key: dict(cells) for key, cells in sim.state.snapshot().items()
            if key.startswith(prefixes) and not key.endswith(ID_KEY_ENDINGS)}


def test_adding_a_domain_changes_nothing_for_the_others(small_content: Content) -> None:
    for i in range(SEEDS):
        seed = f"iso-{i}"
        base = simulate(small_content, seed, [SystemsDomain(), InfectiousDomain()])
        for extra_first in (True, False):
            domains: list[Domain] = [SystemsDomain(), InfectiousDomain()]
            domains.insert(0 if extra_first else 2, NoisyDomain())
            more = simulate(small_content, seed, domains)
            assert any(e.domain == "noisy" for e in more.log)
            both = {"systems", "infectious"}
            assert visible(more, both) == visible(base, both)
            prefixes = ("systems.", "infectious.")
            assert state_of(more, prefixes) == state_of(base, prefixes)


def test_removing_a_domain_keeps_the_remaining_streams(small_content: Content) -> None:
    """Without its partner a domain behaves differently, but its random streams are the same."""
    checked = 0
    for i in range(SEEDS):
        seed = f"iso-{i}"
        both = simulate(small_content, seed, [SystemsDomain(), InfectiousDomain()])
        for domain in (SystemsDomain(), InfectiousDomain()):
            alone = simulate(small_content, seed, [domain])
            assert alone._rngs[domain.name].seed_text == both._rngs[domain.name].seed_text
            for label in ("B01V01:0", "B02V03:17", "B01:5", "init"):
                first = alone._rngs[domain.name].fork(label).random()
                assert first == both._rngs[domain.name].fork(label).random()
                checked += 1
    # A systems-only world has no disease input, so it must match itself with noise added.
    alone = simulate(small_content, "iso-0", [SystemsDomain()])
    noisy = simulate(small_content, "iso-0", [NoisyDomain(), SystemsDomain()])
    assert visible(alone, {"systems"}) == visible(noisy, {"systems"})
    write_report("stream_isolation", {"seeds": SEEDS, "configurations_per_seed": 4,
                                      "stream_checks": checked, "failures": 0})
