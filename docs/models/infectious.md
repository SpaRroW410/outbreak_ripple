# Model: infectious (rash fever)

Code: `engine/domains/infectious/`. Parameters: `content/parameters/infectious.json`
(all illustrative). Rash fever is an invented illness (ADR-006).

## State (per village)

`S` susceptible, `E` exposed, `I` infectious, `R` recovered, `VI` immune by vaccine, `D` dead.
`S+E+I+R+VI+D` always equals the village's starting population (tested every tick).
Also: `vaccinated` (people who received vaccine), `cum_cases` (true), `pending_reports`,
`reported_cases`, `reported_week`, `outbreak_event`, `tracing`, `contact_mult`, `incoming`.

## One week, in order

1. **Arrivals.** Infected travellers queued last week, the planned index cases, and rare
   importations from outside move people from S to E.
2. **Vaccination.** The systems domain decides how many doses are given
   (`systems.session_doses`). Doses go to unvaccinated people; the share who are susceptible
   become immune with probability `vaccine_efficacy x vaccine_potency`. When the immune share
   passes `1 - 1/R0` a "herd threshold reached" event is logged.
3. **Transmission.** Force of infection
   `lambda = beta x contact_mult x I x (1 - tracing x trust) / alive`.
   New infections ~ Binomial(S, 1 - exp(-lambda)); E to I with probability
   `1 - exp(-1/latent_weeks)`; leaving I with probability `1 - exp(-1/infectious_weeks)`,
   of whom a share `case_fatality` die. `beta = R0 x P(leave I per week)`, so one case in a
   fully susceptible village causes R0 cases on average.
4. **Reporting.** A share of new cases is detected (`detection_fraction`, scaled by trust,
   raised by surveillance cards, lowered when block staff are overloaded). Detected cases
   are reported after a random delay with mean `reporting_delay_weeks` (shorter with
   surveillance). An outbreak is declared when reports in two weeks reach the threshold.
5. **Travel.** Each infectious person reaches each neighbouring village with probability
   `travel_rate` (reduced by tracing); arrivals are used next week.

## Assumptions

- Everyone in a village mixes evenly; villages are linked only to their neighbours.
- Weekly time steps; durations are geometric.
- Immunity (natural or vaccine) is lifelong within the one-year run.

## Deliberately ignored

Age structure in transmission, births and other deaths, waning immunity, maternal
antibodies, two-dose schedules, asymptomatic infection, seasonality, hospital capacity,
case management, vaccine failure being remembered for individuals (a vaccinated person who
did not respond is simply still in S).

## Sanity checks (measured by `make sanity`; numbers in `docs/QUALITY_REPORT.md`)

- Outbreaks take off only when R0 is above about 1.
- With R0 fixed, outbreaks stop taking off when the immune share passes about `1 - 1/R0`.

Sampling note: binomial draws use one uniform number each; for large counts a rounded normal
approximation is used (ADR-004).
