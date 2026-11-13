# News

## 2026-11-13: version 0.2.0 (Phases 0, 1 and 2)

- Phase 0: scaffold, `AGENTS.md`, `make check`, CI workflow, content validator, ADR log,
  licence placeholder for content (CC BY-SA 4.0 proposed; owner to confirm).
- Phase 1: engine core (forked RNG streams, clock, state store with declared reads/writes and
  taint tracking, event log with causes and influences, cause-graph utilities, tick pipeline)
  and the district generator.
- Phase 2: `systems` and `infectious` domains, 20 action cards (6 meddle), counterfactual
  diff, public health and ripple scores, 23 draft concept cards with triggers, JSON API,
  mobile web UI running the engine in a Pyodide web worker, UI smoke test.
- Golden file created (`tests/golden/golden.json`).
- All parameters are illustrative with source TODO; all competency entries unverified.
