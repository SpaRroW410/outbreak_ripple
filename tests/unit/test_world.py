"""District generator: structure, determinism, population groups."""

from engine.content import Content
from engine.core.district import AGE_BANDS
from engine.core.rng import Rng
from engine.world.generator import generate_district


def test_structure_within_theme_limits(content: Content) -> None:
    world = content.theme["world"]
    for seed in range(30):
        district = generate_district(Rng(f"w{seed}"), world, content.params)
        assert world["blocks_min"] <= len(district.blocks) <= world["blocks_max"]
        kinds = [facility.kind for facility in district.facilities]
        assert kinds.count("chc") == 1 and kinds.count("district_hospital") == 1
        assert kinds.count("phc") == len(district.blocks)
        assert kinds.count("cold_chain_point") == len(district.blocks)
        names = [village.name for village in district.villages]
        names += [block.name for block in district.blocks]
        assert len(names) == len(set(names))
        for block in district.blocks:
            assert world["villages_min"] <= len(block.village_ids) <= world["villages_max"]
            assert block.anm_count >= 1 and block.medical_officer_count >= 1


def test_villages_have_groups_and_symmetric_neighbours(content: Content) -> None:
    district = generate_district(Rng("groups"), content.theme["world"], content.params)
    for village in district.villages:
        assert len(village.age_bands) == len(AGE_BANDS)
        assert village.population == sum(village.age_bands) > 0
        assert village.kind in ("rural", "urban")
        assert village.asha_count >= 1
        assert village.id not in village.neighbours
        for neighbour in village.neighbours:
            assert village.id in district.village(neighbour).neighbours


def test_same_seed_same_district(content: Content) -> None:
    first = generate_district(Rng("same"), content.theme["world"], content.params)
    second = generate_district(Rng("same"), content.theme["world"], content.params)
    other = generate_district(Rng("other"), content.theme["world"], content.params)
    assert first == second
    assert first != other
