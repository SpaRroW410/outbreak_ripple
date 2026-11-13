"""Generate a fictional district from a seed (SDD 4.3).

Contract
- `generate_district(rng, config, params)` is a pure function of its inputs.
- `config` is the "world" section of a theme file (sizes and name parts).
- `params` supplies the illustrative demographic shares (`world.*` parameters).
- Names are built from name parts; no real place is modelled (ADR-008).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from engine.core.district import AGE_BANDS, Block, District, Facility, Village
from engine.core.domain import Params
from engine.core.ids import block_id, village_id
from engine.core.rng import Rng

_AGE_PARAM_NAMES = ("world.age_share_0_1", "world.age_share_1_5", "world.age_share_5_15",
                    "world.age_share_15_45", "world.age_share_45_60", "world.age_share_60_plus")


def generate_district(rng: Rng, config: Mapping[str, Any], params: Params) -> District:
    """Build blocks, villages, facilities and neighbour links."""
    block_count = rng.randint(config["blocks_min"], config["blocks_max"])
    village_counts = [rng.randint(config["villages_min"], config["villages_max"])
                      for _ in range(block_count)]
    names = _make_names(rng.fork("names"), config, block_count + sum(village_counts))
    blocks: list[Block] = []
    villages: list[Village] = []
    facilities: list[Facility] = [
        Facility("CHC", "chc", "Community Health Centre", ""),
        Facility("DH", "district_hospital", "District Hospital", ""),
    ]
    for index in range(1, block_count + 1):
        bid = block_id(index)
        block_name = names.pop()
        count = village_counts[index - 1]
        ids = [village_id(bid, j) for j in range(1, count + 1)]
        for j, vid in enumerate(ids):
            village_rng = rng.fork(vid)
            sub_centre = f"{bid}SC{j // 2 + 1}"
            villages.append(_make_village(village_rng, config, params, vid, names.pop(), bid,
                                          sub_centre, _neighbours(ids, j, block_count, index)))
        sub_centres = sorted({village.sub_centre_id for village in villages[-count:]})
        for sub_centre in sub_centres:
            facilities.append(Facility(sub_centre, "sub_centre", f"{block_name} sub-centre", bid))
        facilities.append(Facility(f"{bid}PHC", "phc", f"PHC {block_name}", bid))
        facilities.append(Facility(f"{bid}CCP", "cold_chain_point",
                                   f"{block_name} cold chain point", bid))
        blocks.append(Block(bid, block_name, tuple(ids), f"{bid}PHC", f"{bid}CCP",
                            anm_count=len(sub_centres),
                            medical_officer_count=int(params["world.mo_per_phc"]),
                            lab_technician_count=int(params["world.lab_technicians_per_phc"])))
    district_name = rng.fork("district-name").choice(list(config["district_names"]))
    return District(district_name, tuple(blocks), tuple(villages),
                    tuple(sorted(facilities, key=lambda facility: facility.id)))


def _make_names(rng: Rng, config: Mapping[str, Any], needed: int) -> list[str]:
    """Unique place names from prefix + suffix combinations."""
    combos = [prefix + suffix for prefix in config["name_prefixes"]
              for suffix in config["name_suffixes"]]
    if needed > len(combos):
        raise ValueError("not enough name parts in the theme for this district size")
    return rng.sample(combos, needed)


def _neighbours(ids: Sequence[str], j: int, block_count: int, block_index: int) -> tuple[str, ...]:
    """Ring inside the block; the first village also links to adjacent blocks' first village."""
    linked = {ids[(j - 1) % len(ids)], ids[(j + 1) % len(ids)]}
    if j == 0 and block_count > 1:
        previous_block = (block_index - 2) % block_count + 1
        next_block = block_index % block_count + 1
        linked.add(village_id(block_id(previous_block), 1))
        linked.add(village_id(block_id(next_block), 1))
    linked.discard(ids[j])
    return tuple(sorted(linked))


def _make_village(rng: Rng, config: Mapping[str, Any], params: Params, vid: str, name: str,
                  bid: str, sub_centre: str, neighbours: tuple[str, ...]) -> Village:
    """One village or ward with its population groups."""
    urban = rng.chance(config["urban_share"])
    if urban:
        population = rng.randint(config["urban_pop_min"], config["urban_pop_max"])
    else:
        population = rng.randint(config["village_pop_min"], config["village_pop_max"])
    bands = _split(population, [params[name] for name in _AGE_PARAM_NAMES])
    under_five = bands[0] + bands[1]
    older_adults = bands[4] + bands[5]
    adults = bands[3] + bands[4]
    return Village(
        id=vid, name=name, block_id=bid, kind="urban" if urban else "rural",
        age_bands=bands,
        pregnant_women=round(population * params["world.pregnant_share"]),
        undernourished=round(under_five * params["world.undernourished_share_under5"]),
        diabetic_or_hypertensive=round(older_adults * params["world.ncd_share_45_plus"]),
        occupational_exposure=round(adults * params["world.occupational_exposure_share"]),
        water_quality=round(rng.uniform(0.3, 0.95), 3),
        sanitation=round(rng.uniform(0.2, 0.9), 3),
        asha_count=max(1, round(population * params["world.asha_per_1000"] / 1000)),
        sub_centre_id=sub_centre, neighbours=neighbours)


def _split(total: int, shares: Sequence[float]) -> tuple[int, ...]:
    """Split `total` by `shares` (largest remainder) so the parts sum to `total`."""
    scale = sum(shares)
    exact = [total * share / scale for share in shares]
    parts = [int(value) for value in exact]
    order = sorted(range(len(shares)), key=lambda i: (-(exact[i] - parts[i]), i))
    for i in order[: total - sum(parts)]:
        parts[i] += 1
    assert len(parts) == len(AGE_BANDS)
    return tuple(parts)
