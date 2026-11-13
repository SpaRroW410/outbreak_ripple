"""Place identifiers. Plain strings so they sort and serialise predictably.

District "D"; block "B03"; village "B03V05"; facilities such as "B03PHC",
"B03CCP" (cold chain point), "B03SC2" (sub-centre), "CHC", "DH".
"""

from __future__ import annotations

DISTRICT_ID = "D"


def block_id(index: int) -> str:
    """Id of the block with 1-based `index`."""
    return f"B{index:02d}"


def village_id(block: str, index: int) -> str:
    """Id of the village with 1-based `index` inside `block`."""
    return f"{block}V{index:02d}"


def block_of(place_id: str) -> str:
    """Block id that a village or block-level facility id belongs to."""
    return place_id[:3]


def is_village(place_id: str) -> bool:
    """True for ids of the form B03V05."""
    return len(place_id) == 6 and place_id[0] == "B" and place_id[3] == "V"


def is_block(place_id: str) -> bool:
    """True for ids of the form B03."""
    return len(place_id) == 3 and place_id[0] == "B"
