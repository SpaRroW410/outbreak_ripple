# AGENTS.md: read this first

Outbreak Ripple is an offline teaching game about community medicine in a fictional Indian
district. This file orients any coding agent or human maintainer. Keep it short and true.

## Start here (in this order)

1. `AGENTS.md` (this file)
2. `docs/SDD.md`: the design; source of truth
3. `docs/ROADMAP.md`: phases and who builds what
4. `docs/CHECKLIST.md`: what is done and what is open
5. `docs/DECISIONS.md`: why things are the way they are (ADRs)
6. last 20 lines of `NEWS.md`
7. For engine work: `engine/core/domain.py`, `engine/core/state.py`, then one domain
   (`engine/domains/systems/`) and its page in `docs/models/`

Then run `make check` **before changing anything** and report the result.

## How to verify

```
pip install pytest ruff mypy          # dev tools only; the engine has no dependencies
npm install                           # Pyodide (vendored into dist/) and axe-core
npm install --no-save playwright && npx playwright install chromium   # once, for `make ui`
make check                            # everything; about 5 minutes on 4 cores
```

`make check` runs: lint (ruff), type check (mypy strict), file sizes, content validation,
coupling doc freshness, unit tests, determinism, stream isolation, causality, counterfactual,
conservation, model sanity, butterfly, balance, web build, UI smoke test, quality report.
Single targets: `make unit`, `make butterfly`, `make ui`, ... (see `Makefile`).
Measured numbers land in `reports/` and `docs/QUALITY_REPORT.md` (generated; do not edit).
If Playwright is already installed globally with its own browser, do not install it again.

## Rules (non-negotiable)

1. **Dependency rule.** `engine/` is pure Python standard library, no I/O, and never imports
   `web/` or `tools/`. Inside the engine, imports point downward only:
   `core` < `world` < `domains` < `actions` < `scoring` < `assess` < top-level modules
   (`registry`, `runner`, `game`, `results`, `api`). Domains never import each other; they
   share information only through state keys declared in `reads` / `writes`.
   `tests/unit/test_dependencies.py` enforces this.
2. **Domain contract.** A domain only touches the keys it declares; the state store raises
   otherwise. Inside `step`, call `ctx.begin_scope()` before working on a place, keep every
   piece of information in the state store (no values carried between scopes in Python
   variables), and write cells every tick even if unchanged. The taint rule (ADR-005) and
   the counterfactual test depend on this. Use `ctx.rng.fork("<place>:<tick>")` for
   randomness; never `random`, time, or `hash()`.
3. **Content governance.** Every parameter in `content/parameters/*.json` has `value`,
   `unit`, `source`, `status`. New parameters are `"status": "illustrative"`,
   `"source": "TODO"`. Agents never write `reviewed` and never set `verified: true`;
   only the owner does.
4. **No invented citations.** Never make up a reference, guideline number or NMC competency
   code. If you are not certain a source is real and says what you claim, write `TODO`.
5. **Data over code.** Parameters, cards, concept cards, strings and quiz items live in
   `content/` and must pass `python -m tools.validate_content`.
6. **File size.** Source files stay under 300 lines (hard limit 500); card handlers under
   40 lines. `python -m tools.check_sizes` enforces this. Type hints and docstrings
   everywhere; no metaprogramming.
7. **Fictional and private.** Fictional places and people only. No network calls, analytics,
   accounts or personal data.
8. **Honesty.** Never say a test passed unless you ran it. Report what does not work.

## When you change something

- Update `docs/CHECKLIST.md` and `NEWS.md`; add an ADR to `docs/DECISIONS.md` for any design
  decision.
- Changed a domain's keys? Run `python -m tools.gen_coupling`.
- Changed behaviour on purpose? Run `python -m tools.update_golden` and say so in `NEWS.md`.
- Adding a domain: one package under `engine/domains/`, one line in `engine/registry.py`,
  parameters, cards, concept cards, `docs/models/<domain>.md`, tests. No other domain's
  files change.

## Map

| Path | What |
|---|---|
| `engine/core/` | rng, clock, state store (declared access, taint), event log, cause graph, pipeline |
| `engine/world/` | district generator |
| `engine/domains/` | `systems`, `infectious` (one package per domain) |
| `engine/actions/` | card effect ops and named handlers |
| `engine/scoring/` | outcome metrics, counterfactual diff, scores, chain explanations |
| `engine/api.py` | JSON API used by the web worker (`docs/API.md`) |
| `content/` | parameters, cards, concepts, competencies, themes, strings |
| `web/` | presentation only (HTML, CSS, JS, Pyodide worker) |
| `tools/` | validation, build, experiments, reports |
| `tests/` | `unit/`, `invariants/` (SDD section 11), `ui/`, `golden/` |
