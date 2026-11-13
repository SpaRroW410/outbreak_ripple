# Model: systems (stock, cold chain, trust, rumours, workload)

Code: `engine/domains/systems/`. Parameters: `content/parameters/systems.json`
(all illustrative).

## State

Per block (PHC / cold chain point): `vaccine_stock` (doses, never negative),
`vaccine_potency` (0 to 1), `cold_chain_ok`, `cold_chain_care` (weeks of extra maintenance),
`workload`, `staff`, `morale`, `overloaded`, `stocked_out`.
Per village: `trust` and `trust_base` (0 to 1), `rumour` (0 to 1), `surveillance` (boost from
cards, fades), `session_doses` (doses given this week), `campaign_doses` (extra doses on
offer), `session_offset`, `session_boost`.

## One week, in order

1. **Deliveries.** Scheduled stock arrivals and rumour spread from neighbours are applied.
2. **Blocks.**
   - Resupply every `resupply_interval_weeks`; new stock is fully potent and is averaged
     with the old stock's potency.
   - Cold chain: breaks with a small weekly probability (lower under maintenance); while
     broken, stored vaccine loses `cold_chain_potency_loss` of its potency per week; repaired
     with a weekly probability. Lost potency never comes back.
   - Workload = (base + per reported case) / staff. Above the threshold staff are
     overloaded: sessions shrink, morale falls, case detection drops (read by `infectious`).
3. **Villages.**
   - A declared outbreak and new deaths push rumours up; occasionally a session is followed
     by a scare about side effects.
   - Rumours: `growth x r x (1 - r) x (1 - trust) - decay x r x trust`. Above the surge
     threshold a "rumour surge" is logged and the rumour reaches neighbours next week
     (a tipping point).
   - Trust drifts back to its usual level and is eroded by rumours; below the collapse
     threshold a "trust collapse" is logged.
   - Sessions: every `session_interval_weeks` each village holds a routine session.
     People wanting vaccine ~ Binomial(unvaccinated, uptake x trust x (1 - rumour)).
     Doses given = min(wanted, session capacity, block stock). Campaign doses from cards add
     to both demand and capacity. No stock: "stock-out" and "session missed" events.

## Assumptions

- Trust and rumour are single numbers per village.
- One vaccine, one dose, no wastage; stock is held at block level only.
- Staff are a single multiplier per block.

## Deliberately ignored

Budget effects on services (ADR-009), drug stock, referral, individual health workers,
open-vial wastage, session micro-plans, vaccine expiry, district store limits, media.

## Coupling

Reads from `infectious`: `vaccinated`, `reported_week`, `outbreak_event`, `D`.
Read by `infectious`: `session_doses`, `vaccine_potency`, `trust`, `surveillance`,
`overloaded`. Full list: `docs/COUPLING.md`.
