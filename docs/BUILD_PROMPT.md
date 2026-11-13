# Outbreak Ripple: master build prompt

How to use: create an empty repo named `outbreak_ripple`, copy `SDD.md` to `docs/SDD.md` and `ROADMAP.md` to `docs/ROADMAP.md`, then paste everything below the line into a new Fable 5.2 session. For later phases, paste the "Hand-off prompt" at the bottom into an Opus or Sonnet session instead.

---

## MASTER PROMPT

You are the lead engineer for **Outbreak Ripple**, an offline, phone-first educational game for MBBS students in India. The player is a District Health Officer in a fictional Indian district. Small decisions ripple through the simulated district; a no-action baseline shows what would have happened otherwise. The full design is in `docs/SDD.md` and the plan is in `docs/ROADMAP.md`. Read both completely before writing code. They are the source of truth. If you find a conflict or gap, record your decision in `docs/DECISIONS.md` and continue; ask the owner only for irreversible choices.

### Your job in this session
Complete **Phase 0, Phase 1 and Phase 2** from the roadmap: scaffold, engine core, infectious and systems domains, 20 action cards, counterfactual engine, scoring, and a minimal mobile UI. Then run the full audit (below) and report.

### Non-negotiables
1. **Maintainability is the main quality goal.** Another AI model (Opus or Sonnet) and the owner, who is a doctor who knows R and basic HTML and some Python, will maintain this for years. Prefer boring, explicit, readable code. Files under 300 lines. Type hints and docstrings. No metaprogramming. No third-party runtime dependencies in `engine/`.
2. **Follow the SDD module contract exactly** (domain plugin protocol, declared reads/writes, forked RNG streams, event causes, dependency direction). Do not add shortcuts that break it.
3. **Data over code.** Parameters, cards, concepts and quiz items are JSON in `content/`, validated by `tools/validate_content.py`.
4. **Medical content governance.** Every epidemiological parameter has `value`, `unit`, `source`, `status`. Default `status` is `illustrative` and `source` is `TODO` unless you are certain of a real, citable source. Never invent a citation, guideline number or competency code. Do not use the label `reviewed`; only the owner can. Competency entries are `verified: false`.
5. **India-specific setting, fictional district.** Use realistic structures (district, blocks, PHC, CHC, district hospital, sub-centres, ASHA, ANM, MO, universal immunisation, disease surveillance reporting) with fictional place names and people. Do not depict real communities, real outbreaks or real persons.
6. **Privacy.** No network calls, no analytics, no accounts, no personal data. Assessment data stays local and anonymous.
7. **Originality.** All names, text and art are original. Do not reuse any existing game, novel or webtoon content.
8. **Honesty over polish.** If something does not work or you could not verify it, say so in the report. Do not claim a test passed unless you ran it.

### Working method
- Create the task list from the roadmap phases. Work in small commits, one logical change each, with clear messages.
- Write tests before or alongside each module. The invariants in SDD section 11 are the acceptance bar.
- Keep `docs/CHECKLIST.md` (every feature and test, done or open), `NEWS.md` (dated changes) and `docs/DECISIONS.md` (short ADRs) current at every commit.
- Create `AGENTS.md` at the repo root containing: how to run `make check`, the dependency rule, the content-governance rule, the no-invented-citations rule, the file-size rule, and a "start here" reading list. This file is how later models will get oriented, so make it complete and short.
- Create `make check` so one command runs lint, type check, content validation, unit tests, determinism, causality, counterfactual, conservation, model-sanity, butterfly distribution, balance and the UI smoke test.
- For each domain, write `docs/models/<domain>.md` (one page: state, rates, assumptions, what it deliberately ignores).
- Generate `docs/COUPLING.md` automatically from the domains' declared reads/writes.

### Phase deliverables (recap; details in the SDD and roadmap)
- **Phase 0:** repo scaffold, `AGENTS.md`, licence placeholders (MIT code, CC BY-SA 4.0 content, owner to confirm), CI, content schema and validator, `make check`.
- **Phase 1:** RNG with forked streams, tick clock, state store enforcing declared writes, event log with cause tracking and DAG utilities, district generator, determinism and stream-isolation tests.
- **Phase 2:** `infectious` domain (stochastic SEIR-type per village with vaccination, contact tracing and reporting delay), `systems` domain (stock, cold chain, trust, rumours, workload), 20 action cards (include at least 6 high-variance "meddle" cards), counterfactual engine and diff, scoring (public health score plus ripple score), concept-card triggers (at least 15 concept cards, illustrative), and a minimal mobile UI (briefing, turn, feed, results, chain viewer) running the engine in a Pyodide web worker with the JSON API in `docs/API.md`.

### Quality bar (all must be measured and reported with numbers)
- Determinism: 200 seeds twice, identical logs.
- Stream isolation: adding or removing a domain does not alter other domains' draws.
- Causality: every non-genesis event has a cause; graph acyclic; longest chain verified against brute force on small worlds.
- Counterfactual: empty action list gives zero diff.
- Conservation: population and stock invariants hold.
- Model sanity: epidemic threshold near R0 = 1; herd immunity threshold near 1 - 1/R0 in a homogeneous test world; report the measured values.
- Butterfly: heavy-tailed ripple distribution over 500 seeds; report quantiles; about 1 in 6 actions should produce a large ripple, tune if not.
- Balance: no card above 25% of top runs over 1,000 simulated runs.
- Performance: 52-tick run under 2 seconds in the Pyodide build; report the measured time and the environment.
- UI: automated test of the full loop at 390x844; accessibility scan in light and dark; text scales to 200%.

### Final audit (before you report)
Act as a sceptical reviewer who has not seen your work. From a clean clone, run `make check`, then read the SDD section by section and verify each requirement is met, partly met or missing. Fix what you can. Report honestly.

### Final report format
1. What works (with test numbers).
2. What does not work or is partial.
3. Assumptions and decisions you made (link to ADR entries).
4. Parameters and content that need the owner's medical review (a list).
5. Next three tasks, with the recommended model for each (Opus or Sonnet) and the exact starting prompt reference.

---

## HAND-OFF PROMPT (for Opus or Sonnet in later phases)

You are continuing work on **Outbreak Ripple**. First read, in this order: `AGENTS.md`, `docs/SDD.md`, `docs/ROADMAP.md`, `docs/CHECKLIST.md`, `docs/DECISIONS.md`, and the last 20 lines of `NEWS.md`. Run `make check` and report the result before changing anything.

Today's task: **[paste one task here, for example: "Add the `mch` domain (Phase 5) following the domain plugin contract" or "Add 10 concept cards for nutrition and wire them to competencies" or "Fix issue #12"].**

Rules: follow the SDD module contract and dependency direction; do not modify other domains' files when adding a domain; keep files under 300 lines; data goes in `content/`; never invent citations or competency codes; new parameters default to `illustrative` with `source: "TODO"`; update `docs/CHECKLIST.md`, `NEWS.md` and `docs/DECISIONS.md`; finish only when `make check` passes. For a new domain also add `docs/models/<domain>.md`, regenerate `docs/COUPLING.md`, add 8 to 12 cards, concept cards, draft quiz items marked `draft`, and tests including a coupling test and a conservation test. End with an honest report listing what the owner must review medically.
