# Outbreak Ripple

An offline, phone-first educational game for MBBS students. You are a District Health Officer in a fictional Indian district. Small decisions ripple through a simulated district, and a no-action baseline run shows what would have happened otherwise.

> **Status: design phase.** This repository currently contains the design documents only. No game code has been written yet.

## Idea

- **Butterfly effect, made visible.** Every event in the simulation records its causes, so after a run you can trace a cause-and-effect chain from your first action to the final outcome.
- **Counterfactual replay.** The same seed is run with and without your actions, so you see exactly what you changed.
- **Full community medicine, built domain by domain.** Infectious disease epidemiology first, then MCH, nutrition, environment, NCD screening, demography, occupational health and biostatistics.
- **Offline and private.** No accounts, no tracking, no network calls in the default build.
- **Built-in learning assessment (planned).** Anonymous, local pre/post quizzes with an export file, to support a medical-education study.

## Documents

| File | Purpose |
|---|---|
| [`docs/SDD.md`](docs/SDD.md) | Software design document: architecture, domain plugin contract, simulation rules, scoring, assessment, tests |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Phased plan and which AI model or person builds what |
| [`docs/BUILD_PROMPT.md`](docs/BUILD_PROMPT.md) | Master prompt for the first build session, plus a hand-off prompt for later maintenance sessions |

## Planned technology

Pure Python 3 (standard library) simulation engine, run in the browser through Pyodide, with a mobile-first HTML/CSS/JS interface installable as a PWA. Content (parameters, action cards, concept cards, quiz items) lives in JSON files, not code.

## Important notice about content

This is a teaching simulation of a **fictional** district. It is not a clinical tool and does not predict real outbreaks. Epidemiological parameters are marked `illustrative` until reviewed by a subject expert, and each carries its source. Mapping to NMC competencies will be marked unverified until checked against the official document.

## Contributing

The project is designed to be maintained by humans and AI coding assistants. Before changing anything, read `docs/SDD.md` and `docs/ROADMAP.md`. Once code exists, `make check` must pass before any change is merged.

## Author

Dr. Mukul Maheshwari, Department of Community Medicine, Rajshree Medical Research Institute, Bareilly, India.

## Licence

Code and documents: [MIT](LICENSE). A separate licence for educational content (for example CC BY-SA 4.0) may be added once the content exists.
