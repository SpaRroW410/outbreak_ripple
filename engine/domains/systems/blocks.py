"""Block-level weekly update: resupply, cold chain, workload and morale."""

from __future__ import annotations

from engine.core.district import Block
from engine.core.domain import TickContext
from engine.domains.systems import keys as k


def step_block(ctx: TickContext, block: Block) -> None:
    """Advance one block by one week. The caller has opened a scope."""
    rng = ctx.rng.fork(f"{block.id}:{ctx.tick}")
    fail_draw = rng.random()
    repair_draw = rng.random()
    _resupply(ctx, block)
    _cold_chain(ctx, block, fail_draw, repair_draw)
    _workload(ctx, block)


def _resupply(ctx: TickContext, block: Block) -> None:
    """Routine delivery from the district vaccine store every few weeks."""
    state, params = ctx.state, ctx.params
    interval = int(params["systems.resupply_interval_weeks"])
    stock = state.count(k.VACCINE_STOCK, block.id)
    potency = state.num(k.VACCINE_POTENCY, block.id)
    if ctx.tick > 0 and ctx.tick % interval == 0:
        population = ctx.district.block_population(block.id)
        doses = round(population * params["systems.resupply_doses_per_1000"] / 1000)
        potency = (stock * potency + doses) / max(1, stock + doses)
        stock += doses
    state.set(k.VACCINE_STOCK, block.id, stock)
    state.set(k.VACCINE_POTENCY, block.id, round(potency, 4))
    stocked_out = state.count(k.STOCKED_OUT, block.id)
    state.set(k.STOCKED_OUT, block.id, stocked_out if stock == 0 else 0)


def _cold_chain(ctx: TickContext, block: Block, fail_draw: float, repair_draw: float) -> None:
    """Random breakdowns; while broken, stored vaccine loses potency every week."""
    state, params = ctx.state, ctx.params
    working = state.count(k.COLD_CHAIN_OK, block.id)
    care = state.count(k.COLD_CHAIN_CARE, block.id)
    potency = state.num(k.VACCINE_POTENCY, block.id)
    last_failure = state.count(k.COLD_CHAIN_EVENT, block.id)
    fail_probability = params["systems.cold_chain_failure_probability"]
    if care > 0:
        fail_probability *= params["systems.cold_chain_care_factor"]
    if working == 1 and fail_draw < fail_probability:
        working = 0
        event = ctx.emit("systems.cold_chain_failure", block.id, {}, [ctx.genesis_id])
        last_failure = event.id
    elif working == 0:
        potency *= 1.0 - params["systems.cold_chain_potency_loss"]
        if repair_draw < params["systems.cold_chain_repair_probability"]:
            working = 1
            ctx.emit("systems.cold_chain_repaired", block.id,
                     {"potency": round(potency, 2)}, [last_failure])
    state.set(k.COLD_CHAIN_OK, block.id, working)
    state.set(k.COLD_CHAIN_CARE, block.id, max(0, care - 1))
    state.set(k.COLD_CHAIN_EVENT, block.id, last_failure)
    state.set(k.VACCINE_POTENCY, block.id, round(potency, 4))


def _workload(ctx: TickContext, block: Block) -> None:
    """Workload rises with reported cases; overload dents morale."""
    state, params = ctx.state, ctx.params
    cases = 0
    cause = ctx.genesis_id
    for village_id in block.village_ids:
        cases += int(state.get_or(k.INF_REPORTED_WEEK, village_id, 0))
        cause = max(cause, int(state.get_or(k.INF_OUTBREAK_EVENT, village_id, 0)))
    staff = state.num(k.STAFF, block.id)
    morale = state.num(k.MORALE, block.id)
    overloaded = state.count(k.OVERLOADED, block.id)
    work = params["systems.workload_base"] + params["systems.workload_per_case"] * cases
    workload = work / max(0.1, staff)
    if overloaded == 0 and workload >= params["systems.overload_threshold"]:
        overloaded = 1
        ctx.emit("systems.staff_overload", block.id, {"workload": round(workload, 2)}, [cause])
    elif overloaded == 1 and workload < params["systems.overload_recovered"]:
        overloaded = 0
        ctx.emit("systems.staff_recovered", block.id, {"workload": round(workload, 2)}, [cause])
    morale += params["systems.morale_recovery_rate"] * (0.7 - morale)
    if overloaded == 1:
        morale -= params["systems.morale_loss_overloaded"]
    state.set(k.WORKLOAD, block.id, round(workload, 4))
    state.set(k.OVERLOADED, block.id, overloaded)
    state.set(k.MORALE, block.id, round(min(1.0, max(0.0, morale)), 4))
