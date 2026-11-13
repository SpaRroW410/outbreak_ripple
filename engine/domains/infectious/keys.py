"""State keys of the infectious domain (all village cells). See docs/models/infectious.md."""

S = "infectious.S"  # susceptible
E = "infectious.E"  # exposed (infected, not yet infectious)
I = "infectious.I"  # infectious  # noqa: E741
R = "infectious.R"  # recovered and immune
VI = "infectious.VI"  # immune through vaccination
D = "infectious.D"  # died of the disease
VACCINATED = "infectious.vaccinated"  # people who have received the vaccine
CUM_CASES = "infectious.cum_cases"  # true cases so far (hidden from the player)
PENDING_REPORTS = "infectious.pending_reports"  # detected, not yet reported
REPORTED_CASES = "infectious.reported_cases"  # reported so far
REPORTED_WEEK = "infectious.reported_week"  # reported this week
REPORTED_LAST_WEEK = "infectious.reported_last_week"
OUTBREAK_EVENT = "infectious.outbreak_event"  # id of the declaration event, 0 if none
OUTBREAK_OVER = "infectious.outbreak_over"  # 1 once a declared outbreak has ended
LAST_EVENT = "infectious.last_event"  # latest disease event here (cause of the next one)
SEED_TICK = "infectious.seed_tick"  # week the index cases appear, -1 for none
TRACING = "infectious.tracing"  # 0..1 contact tracing effort (cards set it; it fades)
CONTACT_MULT = "infectious.contact_mult"  # multiplier on contact rate (school closure)
DEATH_MILESTONE = "infectious.death_milestone"  # index of the next death milestone
PROTECTED = "infectious.protected"  # 1 once immunity passed the herd threshold
INCOMING = "infectious.incoming"  # infected travellers arriving next week
INCOMING_CAUSE = "infectious.incoming_cause"  # event id behind those travellers

ALL_KEYS = (S, E, I, R, VI, D, VACCINATED, CUM_CASES, PENDING_REPORTS, REPORTED_CASES,
            REPORTED_WEEK, REPORTED_LAST_WEEK, OUTBREAK_EVENT, OUTBREAK_OVER, LAST_EVENT,
            SEED_TICK, TRACING, CONTACT_MULT, DEATH_MILESTONE, PROTECTED, INCOMING,
            INCOMING_CAUSE)

# Keys owned by the systems domain that infectious reads (declared coupling).
SYS_SESSION_DOSES = "systems.session_doses"
SYS_VACCINE_POTENCY = "systems.vaccine_potency"
SYS_TRUST = "systems.trust"
SYS_SURVEILLANCE = "systems.surveillance"

WRITES = frozenset(ALL_KEYS)
READS = frozenset({SYS_SESSION_DOSES, SYS_VACCINE_POTENCY, SYS_TRUST, SYS_SURVEILLANCE})
