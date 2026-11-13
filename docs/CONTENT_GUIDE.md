# Content guide

Everything the game says or assumes is data under `content/`. After any edit run
`python -m tools.validate_content` (also part of `make check`).

## Parameters: `content/parameters/<domain>.json`

```json
"infectious.r0": {"value": 3.0, "unit": "...", "source": "TODO", "status": "illustrative", "note": "..."}
```

- `status`: `illustrative` (default), `sourced` (a real, checked citation is in `source`),
  `reviewed` (**owner only**).
- No source known: `"source": "TODO"` and `"status": "illustrative"`. Never invent a citation.

## Cards: `content/cards/*.json`

`id, name, family, description, cost {budget, action_points}, targets, effects[], concepts[]`.
- `family`: surveillance, immunisation, communication, staffing, investigation, meddle.
- `targets`: village, block or district.
- `effects`: see the op list at the top of `engine/actions/ops.py`. Complex behaviour is a
  named handler in `engine/actions/handlers.py` (`{"op": "handler", "name": "..."}`).
- `concepts`: ids of concept cards the card demonstrates (at least one).

## Concept cards: `content/concepts/*.json`

`id, title, body, competency, parameters[], status`. `status` is `draft` until the owner
reviews it. `parameters` lists the parameters the text depends on; the UI badge says
"reviewed" only when the card and all of those parameters are reviewed.

## Competencies: `content/competencies.json`

`id, code, official_text, working_topic, verified, note`. Until the owner copies the code
and wording from the official NMC document, `code` and `official_text` stay `"TODO"` and
`verified` stays `false`. The validator rejects anything else.

## Themes: `content/themes/<id>.json`

Clock, turn rules, world size and name parts, scoring weights, event weights for the
explain screen, and which event kinds are hidden from the feed.

## Strings: `content/i18n/en.json`

UI text and one sentence per event kind (`event.<kind>`), with `{place}` and payload fields
as placeholders.

## Quiz items: `content/quizzes/*.json` (Phase 3)

`id, stem, options[], answer (index), rationale, competency, difficulty, form (A|B), status (draft|reviewed)`.
Agent-written items are `draft`.
