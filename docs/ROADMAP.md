# Outbreak Ripple: Roadmap

Keep in `docs/ROADMAP.md`. Phases ship independently and each ends with a playable build. Durations are rough effort estimates for one person supervising AI agents, not commitments.

## Model routing (who builds what)

| Work | Suggested model | Why |
|---|---|---|
| Architecture, engine core, determinism, counterfactual, causality graph, cross-domain coupling, final audits | Fable 5.2 | Hard reasoning, long-horizon correctness, test design |
| New domain modules (MCH, nutrition, NCD, ...) built from the plugin contract | Opus | Needs domain-model judgement but follows an established pattern |
| Content (cards, concept cards, i18n), UI screens, CSS, build and deploy scripts, bug fixes, test additions, doc upkeep | Sonnet | Well-specified, repetitive, high volume |
| Medical review of parameters, concepts and quiz items | You (owner) | Subject expertise cannot be delegated |

Hand-off rule: when switching models, the new agent first reads `AGENTS.md`, `docs/SDD.md`, `docs/CHECKLIST.md` and the last 20 lines of `NEWS.md`, then runs `make check` before changing anything.

## Phase 0: Foundations (about 1 week)
- Repo scaffold, `AGENTS.md`, licence, `make check`, CI, content schema and validator, ADR log.
- Exit: empty engine passes determinism test; CI green.

## Phase 1: Engine core (2 to 3 weeks) [Fable]
- RNG with forked streams, clock, state store with declared reads/writes, event log with causes, cause-graph utilities, district generator.
- Exit: determinism, stream isolation, causality and conservation tests pass on 200 seeds.

## Phase 2: Infectious domain and first playable (3 to 4 weeks) [Fable core, Sonnet UI]
- Stochastic SEIR-type villages with vaccination, surveillance delay, contact tracing; systems domain (stock, cold chain, trust, rumours); 20 action cards; counterfactual and scoring; minimal mobile UI (briefing, turn, feed, results, chain viewer).
- Exit: a student can finish a 6-turn run on a phone; baseline diff works; model sanity tests pass (epidemic threshold, herd immunity threshold).

## Phase 3: Concept layer and assessment (2 to 3 weeks) [Sonnet, owner review]
- Concept cards tied to competencies, Explain screen, quiz bank loader, consent, pre/post flow, export.
- Exit: full study flow works offline; export schema validated; owner has reviewed first 20 concept cards and 20 quiz items.

## Phase 4: Static build and pilot (1 to 2 weeks)
- Pyodide build, PWA, GitHub Pages deployment, performance and accessibility tests.
- Pilot with 10 to 20 students (with approval); collect usability feedback.
- Exit: performance budget met; pilot issues triaged into the checklist.

## Phase 5: Domain expansion, one at a time (each 2 to 3 weeks) [Opus]
Order of priority (adjust after the pilot): MCH, nutrition, environment (water and sanitation couples with infectious), NCD screening, demography, occupational, biostat_lab.
- Each domain ships with: model doc, parameters (illustrative), 8 to 12 cards, concept cards, quiz items (draft), tests, and updated COUPLING.md.
- Exit per domain: `make check` green, coupling tests pass, owner review scheduled.

## Phase 6: Research study (parallel from Phase 4)
- Obtain ethics approval, finalise consent, run a pre/post study (game vs standard teaching) in MBBS batches, analyse in R, write the medical-education paper.
- Exit: manuscript draft and open dataset (anonymous).

## Phase 7: Polish and release (2 weeks)
- Hindi strings, content review pass, release notes, citation file (CITATION.cff), Zenodo DOI, public repo, short teaching guide for faculty.

## Phase 8: Long-term maintenance (ongoing) [Sonnet by default, Opus for new domains]
- Monthly: dependency check (Pyodide version), content parameter review, issue triage.
- Annual: curriculum alignment check against NMC updates.
- Rule: no change merges unless `make check` passes and CHECKLIST/NEWS are updated.

## Milestone summary

| Milestone | Deliverable | Gate |
|---|---|---|
| M0 | Scaffold and CI | CI green |
| M1 | Engine core | Invariant tests pass |
| M2 | First playable (infectious) | Student completes a run on phone |
| M3 | Assessment flow | Export validated |
| M4 | Pilot build | Performance and accessibility met |
| M5 to M11 | One domain each | `make check` plus coupling tests |
| M12 | Release | Owner content review complete |

## Risks to watch each phase
- Scope creep: if a domain is not on the list above, it waits.
- Simulation complexity: if a model needs more than one page to explain, simplify it.
- Content accuracy: nothing is labelled "reviewed" without the owner's sign-off.
