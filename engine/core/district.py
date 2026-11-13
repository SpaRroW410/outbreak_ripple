"""Static description of the simulated district (never changes during a run).

Contract: plain frozen dataclasses. Anything that changes over time lives in
the state store, not here. Built by `engine/world/generator.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

AGE_BANDS: tuple[str, ...] = ("0-1", "1-5", "5-15", "15-45", "45-60", "60+")


@dataclass(frozen=True)
class Village:
    """A village (rural) or ward (urban) with its population groups."""

    id: str
    name: str
    block_id: str
    kind: str  # "rural" or "urban"
    age_bands: tuple[int, ...]  # people per entry of AGE_BANDS
    pregnant_women: int
    undernourished: int
    diabetic_or_hypertensive: int
    occupational_exposure: int
    water_quality: float  # 0 (unsafe) to 1 (safe); used by later domains
    sanitation: float  # 0 (poor) to 1 (good); used by later domains
    asha_count: int
    sub_centre_id: str
    neighbours: tuple[str, ...]

    @property
    def population(self) -> int:
        """Total people at the start of the run."""
        return sum(self.age_bands)


@dataclass(frozen=True)
class Facility:
    """A health facility: sub_centre, phc, chc, district_hospital, cold_chain_point."""

    id: str
    kind: str
    name: str
    block_id: str  # "" for district-level facilities


@dataclass(frozen=True)
class Block:
    """An administrative block served by one PHC."""

    id: str
    name: str
    village_ids: tuple[str, ...]
    phc_id: str
    cold_chain_point_id: str
    anm_count: int
    medical_officer_count: int
    lab_technician_count: int


@dataclass(frozen=True)
class District:
    """The whole map. Lookups are by id; iteration order is sorted by id."""

    name: str
    blocks: tuple[Block, ...]
    villages: tuple[Village, ...]
    facilities: tuple[Facility, ...]
    _village_index: dict[str, Village] = field(default_factory=dict, repr=False, compare=False)
    _block_index: dict[str, Block] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        for village in self.villages:
            self._village_index[village.id] = village
        for block in self.blocks:
            self._block_index[block.id] = block

    def village(self, village_id: str) -> Village:
        """Village by id (KeyError if unknown)."""
        return self._village_index[village_id]

    def block(self, block_id: str) -> Block:
        """Block by id (KeyError if unknown)."""
        return self._block_index[block_id]

    def villages_in(self, block_id: str) -> tuple[Village, ...]:
        """Villages of one block, sorted by id."""
        return tuple(self._village_index[v] for v in self._block_index[block_id].village_ids)

    def block_population(self, block_id: str) -> int:
        """Starting population of a block."""
        return sum(village.population for village in self.villages_in(block_id))

    @property
    def population(self) -> int:
        """Starting population of the district."""
        return sum(village.population for village in self.villages)
