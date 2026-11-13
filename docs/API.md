# Engine JSON API

The UI talks to the engine only through `engine/api.py` (`Session.handle_json`), running in
a web worker (`web/js/worker.js`, wrapped by `web/js/bridge.js`).

Request: `{"cmd": "<name>", "args": {...}}`.
Reply: `{"ok": true, "result": ...}` or `{"ok": false, "error": "message"}`.

| Command | Args | Result |
|---|---|---|
| `new_game` | `seed` (text) | state |
| `get_state` | none | state (with an empty `feed`) |
| `play_turn` | `plays`: list of `{card_id, target}` (at most `max_cards`) | state; `feed` = visible events of the weeks just simulated |
| `get_chain` | `event_id` | `{event_id, nodes}`: the event, all its causes back to the start, and their direct influences |
| `get_diff` | none (after the last turn) | results |
| `export_session` | `concepts_viewed`: list of concept ids (optional) | export |
| `benchmark` | `seed` | `{events, digest}` of one no-action run (used by the performance test) |

## State

`seed, turn, turns, tick, ticks, finished, budget, action_points, max_cards`,
`theme {title, disease_name, disease_note}`,
`district {name, population, blocks[]}` where a block is
`{id, name, vaccine_stock, cold_chain_ok, overloaded, villages[]}` and a village is
`{id, name, kind, population, reported_cases, reported_week, deaths, coverage, trust, rumour, outbreak}`,
`totals {reported_cases, deaths, coverage}`,
`hand[]` of cards `{id, name, family, description, budget_cost, action_points, target_kind, concepts}`,
`feed[]` of events.

The player sees reported cases only; true cases are in the results.

## Event

`{id, tick, kind, place_id, place_name, payload, causes, influences, domain}`.
`causes` are real mechanisms. `influences` are earlier events downstream of a player action
that may have shifted this event (ADR-005). Sentences for each kind are in
`content/i18n/en.json` under `event.<kind>`.

## Results (`get_diff`)

`player` and `baseline`: `{cases, reported_cases, deaths, coverage, coverage_gap, mean_trust, outbreaks, stockouts, sessions_missed}`;
`deltas {cases_averted, deaths_averted, coverage_gain, gap_reduction, trust_gain, stockouts_added}`;
`health_score {deaths_part, cases_part, coverage_part, equity_part, total}`;
`ripple_score {reach, depth, surprise, total}`; `ripple_size`;
`added` and `prevented`: event kind -> count (only in the player's run / only in the baseline);
`chains[]`: `{events[], concept}` where concept is
`{id, title, body, badge, competency}` or null, and badge is `illustrative` or `reviewed`;
`series {player_cases[], baseline_cases[]}` (cumulative true cases per week).

## Export (`export_session`)

`{schema_version, engine_version, content_version, seed, plays[], scores, counters {cards_by_family, concepts_viewed}}`.
No personal data. The participant code and quiz answers are added in Phase 3.
