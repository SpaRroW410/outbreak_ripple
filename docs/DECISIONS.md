# Decisions (ADR log)

Short records: context, decision, consequences. Newest at the bottom.

## ADR-001: Player actions are root events in the cause graph
Context: SDD 4.5 says causes are "an earlier event id or a player action id".
Decision: each played card is logged as an event of kind `player.action` (no cause needed,
like the genesis event). Consequences: one id space; `blast_radius(action_id)` is just a
graph query.

## ADR-002: Layering inside the engine
Context: the SDD says "dependencies point downward only" but `core/domain.py` (the plugin
contract) must mention the district types.
Decision: the static district dataclasses live in `engine/core/district.py`;
`engine/world/` holds only the generator. Order: core < world < domains < actions < scoring
< assess < top-level modules. Enforced by `tests/unit/test_dependencies.py`.

## ADR-003: `init_state(world, rng)` receives a WorldView
Context: the SDD signature returns nothing and passes no state.
Decision: `world` is a `WorldView` (district + the domain's state view + parameters).
`TickContext` adds `begin_scope`, `emit`, `schedule`, `inbox`.

## ADR-004: Binomial sampling by inversion, one uniform per draw
Context: the counterfactual compares two runs on the same streams. A standard sampler
gives unrelated results when its inputs differ slightly, so every tiny change would
re-roll the epidemic.
Decision: `Rng.binomial` uses exactly one uniform and is monotone in it (exact inversion
for small means, rounded normal approximation when n*min(p,1-p) > 30).
Consequences: small causes give small effects unless a threshold is crossed; the normal
approximation is not exact (acceptable for teaching; documented in the model page).

## ADR-005: Taint tracking in the state store; causes versus influences
Context: SDD 11 demands that a single card changes the run "only downstream of the action".
Hand-written cause links cannot guarantee that.
Decision: the state store tracks, per cell, a "taint": the latest event downstream of a
player action that may have influenced the cell. Reading a tainted cell taints the scope;
writes carry the scope's taint. When a domain emits an event in a tainted scope and none of
its real causes is downstream of an action, the taint is attached as an **influence**
(`Event.influences`), not as a cause. `causes` stay hand-written mechanisms.
Consequences: (1) tested guarantee: every event and every state cell that differs from the
baseline is downstream of an action; (2) the chain viewer shows causes, and shows influences
separately as "may also have been shifted by"; (3) taint is conservative: it spreads to
neighbouring villages every tick, so late in a run most events carry an influence link;
(4) the event schema has one field more than SDD 4.5 (`influences`); (5) domains must follow
the scope discipline in AGENTS.md rule 2.

## ADR-006: The illness is invented ("rash fever")
Context: gameplay needs R0 around 3 with weekly ticks; labelling that "measles" would teach
wrong numbers.
Decision: the Phase 2 theme uses an invented vaccine-preventable illness; all parameters are
`illustrative` with `source: "TODO"`. The owner may later map themes to real diseases with
sourced parameters.

## ADR-007: Cross-domain coupling uses state keys only
Decision: domains do not listen to each other's events. `infectious` exposes
`infectious.outbreak_event`, `infectious.D`, ... as state; `systems` reads them. Scheduled
events are delivered only to the domain named by the kind's prefix.
Consequences: `docs/COUPLING.md` (generated from `reads`/`writes`) is the complete list.

## ADR-008: Place names are generated from name parts
Decision: district, block and village names combine prefixes and suffixes listed in the
theme file. No real place is modelled; a generated name may coincide with a real village
name by chance.

## ADR-009: Budget and action points are turn accounting
Context: SDD 4.3 lists budget under systems state.
Decision: in Phase 2 budget does not influence the simulation, so it lives in
`engine/game.py`, not the state store. Move it into `systems` when a mechanic needs it.

## ADR-010: Definitions used by the quality bars
- Diff: two events match when tick, kind and place match; ripple size = events in exactly
  one run (player action events excluded).
- Butterfly "large ripple": ripple size >= 10 after one random card.
- Balance: share of a card among all cards played in the top 10% of 1,000 random-policy runs.
- Surprise: 1 - share of no-action runs with other dice (baseline + 5 noise runs) whose true
  case count is at least as far from their median as the player's.
- Ripple depth counts only the action and events the baseline does not have.

## ADR-011: Content text is English inside content files
Context: SDD 9 wants strings in `content/i18n/en.json`.
Decision: UI strings and event sentences are in `i18n/en.json`. Card names/descriptions and
concept text stay in their own JSON files (English); a per-language overlay is planned for
Phase 7. Competency entries use local ids with `code: "TODO"` until the owner copies the
official codes.

## ADR-012: No service worker yet
Decision: PWA caching is Phase 4 (roadmap). Phase 2's build is a static folder (`dist/`)
that works from any static server with no network calls.

## ADR-013: Hidden information
Decision: during play the API's feed omits `infectious.index_case` and
`infectious.importation` (theme key `feed_hidden_kinds`) and the dashboard shows reported
cases only. True case counts appear on the results screen. Deaths, coverage, trust and stock
are shown as known to the DHO.
