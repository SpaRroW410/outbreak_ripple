"""Surveillance: detection, reporting delay and outbreak declaration.

Only a fraction of cases is ever detected (the iceberg), and detected cases
reach the reporting system after a delay. The player sees reported cases only.
"""

from __future__ import annotations

import math

from engine.core.district import Village
from engine.core.domain import TickContext
from engine.core.rng import Rng
from engine.domains.infectious import keys as k


def report_cases(ctx: TickContext, village: Village, new_cases: int, rng: Rng) -> None:
    """Move new cases into the reporting pipeline and declare outbreaks."""
    state, params = ctx.state, ctx.params
    vid = village.id
    trust = float(state.get_or(k.SYS_TRUST, vid, 0.6))
    boost = float(state.get_or(k.SYS_SURVEILLANCE, vid, 0.0))
    detection = params["infectious.detection_fraction"] * (0.5 + 0.5 * trust)
    detection = min(1.0, detection + params["infectious.surveillance_detection_gain"] * boost)
    delay = params["infectious.reporting_delay_weeks"]
    delay *= 1.0 - params["infectious.surveillance_delay_reduction"] * boost
    p_report = 1.0 - math.exp(-1.0 / max(0.1, delay))
    pending = state.count(k.PENDING_REPORTS, vid) + rng.binomial(new_cases, detection)
    reported_now = rng.binomial(pending, p_report)
    reported_before = state.count(k.REPORTED_CASES, vid)
    last_week = state.count(k.REPORTED_WEEK, vid)
    declared = state.count(k.OUTBREAK_EVENT, vid)
    last_event = state.count(k.LAST_EVENT, vid)
    if reported_before == 0 and reported_now > 0:
        event = ctx.emit("infectious.first_report", vid, {"cases": reported_now}, [last_event])
        last_event = event.id
    threshold = params["infectious.outbreak_threshold_reported"]
    if declared == 0 and reported_now + last_week >= threshold:
        event = ctx.emit("infectious.outbreak_declared", vid,
                         {"cases": reported_now + last_week}, [last_event])
        last_event = event.id
        declared = event.id
    state.set(k.PENDING_REPORTS, vid, pending - reported_now)
    state.set(k.REPORTED_CASES, vid, reported_before + reported_now)
    state.set(k.REPORTED_LAST_WEEK, vid, last_week)
    state.set(k.REPORTED_WEEK, vid, reported_now)
    state.set(k.OUTBREAK_EVENT, vid, declared)
    state.set(k.LAST_EVENT, vid, last_event)
