"""State keys of the systems domain. See docs/models/systems.md.

Village cells unless marked (block).
"""

TRUST = "systems.trust"  # 0..1 trust in the health system
TRUST_BASE = "systems.trust_base"  # level trust drifts back to
TRUST_LOW = "systems.trust_low"  # 1 while trust is collapsed
RUMOUR = "systems.rumour"  # 0..1 rumour level
RUMOUR_HIGH = "systems.rumour_high"  # 1 while a rumour surge is on
RUMOUR_CAUSE = "systems.rumour_cause"  # event id that last pushed rumours up
SURVEILLANCE = "systems.surveillance"  # 0..1 boost from surveillance cards
SESSION_DOSES = "systems.session_doses"  # doses given this week (read by infectious)
SESSION_OFFSET = "systems.session_offset"  # which week of the cycle the session falls on
SESSION_BOOST = "systems.session_boost"  # turnout multiplier for routine sessions
CAMPAIGN_DOSES = "systems.campaign_doses"  # extra doses on offer this week
SEEN_OUTBREAK = "systems.seen_outbreak"  # last outbreak event the village reacted to
SEEN_DEATHS = "systems.seen_deaths"  # deaths the village has already reacted to

VACCINE_STOCK = "systems.vaccine_stock"  # (block) doses at the cold chain point
VACCINE_POTENCY = "systems.vaccine_potency"  # (block) 0..1, read by infectious
STOCK_CAUSE = "systems.stock_cause"  # (block) event id that last changed stock unusually
STOCKED_OUT = "systems.stocked_out"  # (block) 1 while a stock-out episode is on
COLD_CHAIN_OK = "systems.cold_chain_ok"  # (block) 1 working, 0 broken
COLD_CHAIN_CARE = "systems.cold_chain_care"  # (block) weeks of extra maintenance left
COLD_CHAIN_EVENT = "systems.cold_chain_event"  # (block) id of the last failure event
WORKLOAD = "systems.workload"  # (block) work divided by staff; 1.0 is full stretch
STAFF = "systems.staff"  # (block) staff strength multiplier
MORALE = "systems.morale"  # (block) 0..1
OVERLOADED = "systems.overloaded"  # (block) 1 while staff are overloaded

VILLAGE_KEYS = (TRUST, TRUST_BASE, TRUST_LOW, RUMOUR, RUMOUR_HIGH, RUMOUR_CAUSE, SURVEILLANCE,
                SESSION_DOSES, SESSION_OFFSET, SESSION_BOOST, CAMPAIGN_DOSES, SEEN_OUTBREAK,
                SEEN_DEATHS)
BLOCK_KEYS = (VACCINE_STOCK, VACCINE_POTENCY, STOCK_CAUSE, STOCKED_OUT, COLD_CHAIN_OK,
              COLD_CHAIN_CARE, COLD_CHAIN_EVENT, WORKLOAD, STAFF, MORALE, OVERLOADED)

# Keys owned by the infectious domain that systems reads (declared coupling).
INF_VACCINATED = "infectious.vaccinated"
INF_REPORTED_WEEK = "infectious.reported_week"
INF_OUTBREAK_EVENT = "infectious.outbreak_event"
INF_DEATHS = "infectious.D"

WRITES = frozenset(VILLAGE_KEYS + BLOCK_KEYS)
READS = frozenset({INF_VACCINATED, INF_REPORTED_WEEK, INF_OUTBREAK_EVENT, INF_DEATHS})
