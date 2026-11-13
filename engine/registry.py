"""The domain registry: the single place that lists which domains are loaded.

Adding a domain = one import and one line in `build_domains`. Order matters:
it is the order in which domains step each tick (systems first, SDD 4.4).
"""

from __future__ import annotations

from engine.core.domain import Domain
from engine.domains.infectious import InfectiousDomain
from engine.domains.systems import SystemsDomain


def build_domains() -> list[Domain]:
    """Fresh domain objects in step order."""
    return [
        SystemsDomain(),
        InfectiousDomain(),
    ]
