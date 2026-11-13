# Outbreak Ripple

An offline, phone-first educational game for MBBS students. You are a District Health Officer in a fictional Indian district. Small decisions ripple through a simulated district, and a no-action baseline run shows what would have happened otherwise.

> **Status: first playable (version 0.2.0, roadmap Phases 0 to 2).** One invented illness ("rash fever"), two simulation domains, 20 action cards, counterfactual results. All medical parameters are **illustrative** and no content has been reviewed yet. Not a clinical tool.

## Try it

```
npm install                 # fetches Pyodide and axe-core (dev only)
python -m tools.build_web   # builds dist/
python -m tools.serve       # http://127.0.0.1:8000/
```

Requires Python 3.12+ and Node 20+. The built app makes no network calls.

## Verify it

```
pip install pytest ruff mypy
make check
```

See [`AGENTS.md`](AGENTS.md) for the full setup (Playwright for the browser test) and the rules. Measured results of the last run are in [`docs/QUALITY_REPORT.md`](docs/QUALITY_REPORT.md).

## Idea

- **Butterfly effect, made visible.** Every event records its causes, so after a run you can trace what your cards led to.
- **Counterfactual replay.** The same seed is run with and without your actions, so you see exactly what you changed.
- **Full community medicine, built domain by domain.** Infectious disease epidemiology first, then MCH, nutrition, environment, NCD screening, demography, occupational health and biostatistics.
- **Offline and private.** No accounts, no tracking, no network calls.
- **Built-in learning assessment (planned, Phase 3).** Anonymous, local pre/post quizzes with an export file.

## Documents

| File | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Orientation and rules for maintainers (human or AI) |
| [`docs/SDD.md`](docs/SDD.md) | Software design document |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Phased plan |
| [`docs/CHECKLIST.md`](docs/CHECKLIST.md) | What is done, what is open |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Design decisions (ADRs) |
| [`docs/API.md`](docs/API.md) | JSON API between UI and engine |
| [`docs/CONTENT_GUIDE.md`](docs/CONTENT_GUIDE.md) | How to edit parameters, cards and concept cards |
| [`docs/models/`](docs/models/) | One page per simulation model |
| [`docs/COUPLING.md`](docs/COUPLING.md) | Which domain reads which state (generated) |
| [`docs/BUILD_PROMPT.md`](docs/BUILD_PROMPT.md) | Build prompt and hand-off prompt for later sessions |

## Important notice about content

This is a teaching simulation of a **fictional** district. It is not a clinical tool and does not predict real outbreaks. Every epidemiological parameter is marked `illustrative` until reviewed by a subject expert. Mapping to NMC competencies is unverified until checked against the official document.

## Author

Dr. Mukul Maheshwari, Department of Community Medicine, Rajshree Medical Research Institute, Bareilly, India.

## Licence

Code and documents: [MIT](LICENSE). Educational content: CC BY-SA 4.0 proposed, see [`LICENSE-CONTENT.md`](LICENSE-CONTENT.md) (owner to confirm).
