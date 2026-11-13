# Outbreak Ripple: Software Design Document (SDD)

Version 0.1 (design). Owner: Dr. Mukul Maheshwari. Keep this file in `docs/SDD.md` and update it whenever the design changes.

## 1. Purpose and scope

Outbreak Ripple is an offline, phone-first educational game for MBBS students. The player is a District Health Officer (DHO) in a simulated Indian district. Small decisions ripple through the district; a no-action baseline run lets the player see what would have happened otherwise. Scope is full community medicine (PSM): infectious disease epidemiology, MCH, nutrition, NCDs, environment, occupational health, demography, biostatistics and health systems. Delivery is phased (see ROADMAP.md).

Goals
1. Teach community medicine concepts by letting students cause and observe their effects.
2. Make causality visible (cause-and-effect graph and counterfactual replay).
3. Support an anonymous, local pre/post learning assessment for a research study.
4. Stay easy to maintain by humans and by AI coding agents (Sonnet, Opus) over years.

Non-goals: clinical decision support, real surveillance, real patient data, accounts, servers, advertising, real-money mechanics, any network call in the default build.

## 2. Accuracy and content governance (important)

This is a teaching tool in medicine, so wrong content is a real defect.
- Every epidemiological parameter (R0, incubation period, vaccine efficacy, case fatality, coverage targets, schedules, norms) lives in `content/parameters/*.json` with fields: `value`, `unit`, `source` (citation or official document), `status` (`illustrative` | `sourced` | `reviewed`).
- Default status is `illustrative`. Only the owner (subject expert) can promote a parameter to `reviewed`. The UI shows a small "illustrative" badge on any concept card whose parameters are not `reviewed`.
- Agents must never invent a citation. If no source is known, set `source: "TODO"` and `status: "illustrative"`.
- The game simulates a fictional district. It must not claim to predict real outbreaks.
- Concept cards (teaching text) are mapped to NMC CBME community medicine competencies in `content/competencies.json`. Competency codes and wording must be copied from the official NMC document; until verified by the owner, each entry has `verified: false`.

## 3. Architecture overview

```
web/ (HTML, CSS, JS, service worker)        presentation only, no game rules
   |  JSON messages over a small bridge (worker.js <-> Pyodide)
engine/ (pure Python 3 stdlib)              all rules, deterministic, no I/O
   core/        clock, rng, ids, event log, cause graph, state store
   world/       district generator (villages, facilities, people groups)
   domains/     one package per domain (plugins, see section 5)
   actions/     player action cards (effects declared as data + small handlers)
   scoring/     counterfactual diff, score, concept-card triggers
   assess/      quiz bank loader, session recorder, export
content/ (JSON data, no code)               parameters, cards, concepts, quizzes, themes
tests/                                      unit, property, golden, balance, UI
docs/                                       SDD, ROADMAP, CHECKLIST, DECISIONS, NEWS, CONTENT_GUIDE
tools/                                      build_web.py, validate_content.py, balance_report.py
```

Rule: dependencies point downward only. `engine` never imports `web`. `domains` never import each other; they communicate only through the shared state store and events (section 6).

## 4. Core engine design

### 4.1 Determinism
- One seeded PRNG (`random.Random` subclass wrapper `core/rng.py`). Each domain and each village derives its own sub-stream via `rng.fork("domain:village:tick")` so adding a domain does not change other domains' random draws.
- No use of wall-clock time, `hash()` on strings, or dict-order assumptions. Sorted iteration everywhere.
- Same seed + same action list gives an identical event log. This is a tested invariant.

### 4.2 Time
- 1 tick = 1 week. A run = 52 ticks (one year) divided into 6 decision turns (about 8 weeks each). Configurable in `content/themes/*.json`.

### 4.3 World generation (`world/`)
- A district of 6 to 12 blocks, each with 3 to 8 villages or wards (urban and rural mix), a PHC per block, a CHC, a district hospital, sub-centres, and a cold chain point.
- Population groups per village: age bands (0-1, 1-5, 5-15, 15-45, 45-60, 60+), pregnant women, and a small set of attributes (undernourished, diabetic or hypertensive, occupational exposure).
- Health workers: ASHA, ANM, MO, lab technician, with workload and morale.
- Systems state: vaccine stock, cold chain status, drug stock, budget, water source quality, sanitation level, trust in health system, rumour level.

### 4.4 Tick pipeline
```
1  player action effects are applied (turn start only)
2  environment and systems update (stock, water, trust, rumours)
3  each domain.step(ctx) runs in a fixed order (registry order)
4  events emitted by domains are collected, causes attached, thresholds checked
5  tipping-point rules may emit follow-up events (next tick)
6  snapshot metrics recorded
```

### 4.5 Event log and cause graph (signature feature)
- Event: `{id, tick, kind, place_id, payload, causes: [event_id], domain}`.
- Every non-genesis event must list at least one cause (an earlier event id or a player action id). The graph is a DAG by construction (causes must have lower ids).
- Utilities: `ancestors(id)`, `descendants(id)`, `longest_chain(from_id)`, `blast_radius(action_id)` (places, groups, domains touched).

### 4.6 Counterfactual engine
- `run(seed, actions)` and `run(seed, [])` (baseline) use identical RNG streams. `diff(a, b)` reports differences in cases, deaths, coverage, stock-outs, trust, and events that exist only in one run.
- Because streams are forked per domain, a divergence is attributable to the player's action chain, not to random noise. A test asserts that an empty action list produces zero diff.

## 5. Domain plugin contract

Each domain lives in `engine/domains/<name>/` and exposes a class implementing `Domain` (in `engine/core/domain.py`):

```python
class Domain(Protocol):
    name: str                     # "infectious", "mch", ...
    reads: frozenset[str]         # state keys it reads
    writes: frozenset[str]        # state keys it writes
    def init_state(self, world, rng) -> None: ...
    def step(self, ctx: TickContext) -> list[Event]: ...
    def concept_triggers(self) -> list[ConceptTrigger]: ...
```

Rules:
- A domain may only touch the keys it declares in `writes`; the state store raises an error on undeclared writes (tested).
- Cross-domain coupling happens through shared keys (for example water quality written by `environment`, read by `infectious` for diarrhoeal disease). Declared coupling is listed in `docs/COUPLING.md` (generated by `tools/gen_coupling.py` from reads/writes).
- Adding a domain = one new package + one registry line + content files + tests. No existing domain file changes.

Planned domains (phased):
| Domain | Examples of mechanics |
|---|---|
| infectious | stochastic SEIR-type models per village, vaccination, contact tracing, outbreak investigation, surveillance reporting delay |
| mch | ANC visits, institutional delivery, neonatal and maternal outcomes, immunisation schedule coverage |
| nutrition | child growth, SAM and MAM, supplementation, anaemia |
| ncd | screening cascade (screen, confirm, treat, adhere), control rates |
| environment | water quality, sanitation, vector breeding, air and waste |
| occupational | exposure groups, notified occupational diseases |
| demography | births, deaths, migration, pyramid, family planning |
| systems | staff, stock, cold chain, budget, trust, rumours, referral |
| biostat_lab | optional in-game survey and sampling mini-games that reuse the world as population |

Model fidelity: simple, explainable, stochastic compartment and rate models. No fitting to real data in v1. Simplicity beats realism; each model must be explainable on one page of `docs/models/<domain>.md`.

## 6. Player actions

- Action card = JSON declaring: `id`, `name`, `cost` (budget and action points), `targets` (village, block, facility, group), `effects` (a list of declarative effect ops such as `set_state`, `add_state`, `schedule_event`, `inject_rumour`) and `concepts` (concept ids it demonstrates).
- Complex card behaviour goes into small named handlers in `engine/actions/handlers.py` referenced by name from JSON. Maximum handler length 40 lines.
- Card families: Surveillance, Immunisation, Vector and environment, Communication and trust, Staffing and logistics, Screening, MCH services, Investigation (outbreak investigation steps), and "Meddle" cards (small, risky, high-variance nudges: reschedule a session, redirect stock, issue a press note) which is where the butterfly effect shows up.
- Every turn: choose up to 2 cards from a hand of 5. Budget and action points limit spamming.

## 7. Scoring

- Public health score (primary): relative to baseline, weighted sum of deaths averted, cases averted, coverage gained, and inequity gap reduced. Weights in `content/themes`.
- Ripple score (secondary, for fun): reach (places, groups, domains touched) x depth (longest cause chain) x surprise (probability of outcome under baseline-noise runs).
- Explain screen: top three cause chains with one concept card each ("This was herd immunity falling below threshold"), each tagged with its competency code and its `illustrative/reviewed` badge.
- No leaderboards in v1 (privacy). Daily seed supported locally.

## 8. Learning assessment (anonymous, local)

- Quiz bank `content/quizzes/*.json`: item id, stem, options, answer, rationale, competency id, difficulty tag, form (`A` or `B`). Items are authored by or reviewed by the owner; agent-drafted items are marked `draft`.
- Flow: consent screen, random participant code (not linked to name), optional demographic bucket (batch, phase), pre-test form A, play, post-test form B, short usability and engagement questions (for example SUS-style items).
- Storage: `localStorage` only. Export button writes a JSON and CSV file the student shares with the researcher.
- No network, no analytics, no names. Ethics approval and the consent text are the owner's responsibility; a template consent text lives in `docs/CONSENT_TEMPLATE.md` marked "needs IEC review".
- Also record in-game behaviour counters (cards used per family, concepts viewed) in the export, since they support analysis of mechanism.

## 9. Presentation layer

- Mobile-first, 360 to 430px wide, thumb reachable controls, light and dark theme, WCAG AA contrast, reduced-motion support, text scaling to 200%.
- Screens: Home, Briefing (district dashboard with maps as simple tile grid or schematic, not GIS), Turn (hand of cards), Feed (what happened), Chain viewer (cause graph, collapsible), Results (score, diff vs baseline), Concept library, Assessment, Settings, Export.
- Engine runs in a Web Worker via Pyodide; the UI talks to it through a tiny JSON API (`new_game`, `get_state`, `play_turn`, `get_chain`, `get_diff`, `export_session`). The API is documented in `docs/API.md` and is the only coupling point.
- PWA: service worker caches the app shell and Pyodide files for offline use. Static build deployable to GitHub Pages.
- Languages: English first; strings live in `content/i18n/en.json` so Hindi can be added without code changes.

## 10. Maintainability rules (for humans and AI agents)

1. Small files: target under 300 lines, hard limit 500. Small functions with type hints and docstrings.
2. Plain Python only: dataclasses, no metaprogramming, no clever decorators, no third-party runtime dependencies in `engine/`. Test tools (pytest, playwright) are dev-only.
3. Data over code: content and parameters in JSON with a schema checked by `tools/validate_content.py`. CI fails on invalid content.
4. One concept per module and a module header docstring stating its contract.
5. `AGENTS.md` at repo root tells any coding agent: how to run tests, the dependency rule, the content-governance rule, and "never invent citations".
6. Every design decision gets a short ADR in `docs/DECISIONS.md` (context, decision, consequences).
7. Every change updates `docs/CHECKLIST.md` and `NEWS.md`.
8. Golden tests: a fixed seed plus fixed actions produces a stored event-log hash; intentional behaviour changes require updating the golden file with a note in NEWS.
9. One command to verify everything: `make check` (lint, type check, content validation, unit tests, determinism, balance, UI smoke).
10. Feature flags for anything experimental; default off.

## 11. Testing and verification

| Area | Test |
|---|---|
| Determinism | 200 seeds run twice, identical logs and hashes |
| Stream isolation | adding or removing a domain does not change other domains' random draws on the same seed |
| Causality | every non-genesis event has a cause; graph acyclic; longest chain matches brute force on small worlds |
| Counterfactual | empty actions gives zero diff; a single card gives non-zero diff only downstream of the action |
| Conservation | population and stock invariants (people are not created or lost except via births, deaths, migration; stock never negative) |
| Model sanity | each infectious model reproduces known qualitative behaviour (epidemic threshold near R0 = 1, herd immunity threshold approximately 1 - 1/R0 in a homogeneous test world) |
| Butterfly | across 500 seeds with random actions, ripple size is heavy tailed (report quantiles); no-op is zero |
| Balance | no card or card family dominates more than 25% of top-scoring runs over 1,000 simulated runs |
| Content | schema valid, every concept has a competency id, every parameter has a source or TODO, no orphan references |
| Performance | one full 52-tick run under 2 seconds in the Pyodide build on a mid-range phone; initial load under 10 seconds on 4G with caching afterwards |
| UI | automated browser test at 390x844 for the full loop; axe-core accessibility scan in light and dark |
| Assessment | export schema test; participant code is random and not derived from user input |

## 12. Deployment

- `tools/build_web.py` vendors Pyodide and the engine into `dist/`; GitHub Actions publishes to GitHub Pages. A local dev server (`python tools/serve.py`) serves the same files.
- Version string in `engine/__init__.py` and shown in Settings; the session export includes engine and content versions so results from different builds are distinguishable.

## 13. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Medical inaccuracy | content governance (section 2), owner review, visible badges |
| Scope explosion (full community medicine) | domain plugin contract and phased roadmap; each domain ships independently |
| Models too complex to maintain | one-page model docs, simple compartment models, tests for sanity not fit |
| Pyodide load time on phones | cache after first load; lazy-load domains; measure in CI |
| Students game the score without learning | scoring tied to public health outcomes and concept cards; assessment measures learning separately |
| Agent drift in long-term maintenance | AGENTS.md, ADRs, golden tests, strict module contract |
| Research ethics | local-only data, anonymous codes, consent template, owner obtains IEC approval |

## 14. Open items for the owner

1. Verify the competency list against the official NMC CBME document and mark entries `verified`.
2. Review and promote parameters from `illustrative` to `reviewed`.
3. Author or review quiz items (about 10 per priority topic, two parallel forms).
4. Obtain ethics approval before any student data collection.
5. Choose a licence (suggest MIT for code and CC BY-SA 4.0 for content).
