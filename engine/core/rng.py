"""Seeded random numbers with forked sub-streams.

Contract
- An `Rng` is fully described by its seed text. Same text, same numbers.
- `fork(label)` returns an independent stream whose seed text is
  `parent_text + "/" + label`. Forking never consumes numbers from the parent,
  so adding or removing a consumer cannot shift anybody else's draws.
- `binomial` consumes exactly one uniform number per call and is monotone in
  that number. Two runs that reach the same draw with slightly different
  inputs therefore get similar results (common random numbers), which keeps
  the counterfactual comparison clean. See docs/DECISIONS.md ADR-004.
"""

from __future__ import annotations

import hashlib
import math
import random
from statistics import NormalDist

_STANDARD_NORMAL = NormalDist()
_NORMAL_APPROX_MIN = 30.0  # use the normal approximation above this n*p*(1-p) scale


def _seed_int(seed_text: str) -> int:
    """Turn seed text into a 64-bit integer without using the salted hash()."""
    digest = hashlib.sha256(seed_text.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


class Rng(random.Random):
    """A `random.Random` whose identity is a piece of seed text."""

    def __init__(self, seed_text: str) -> None:
        super().__init__(_seed_int(seed_text))
        self.seed_text = seed_text

    def fork(self, label: str) -> Rng:
        """Return an independent sub-stream named by `label`."""
        return Rng(f"{self.seed_text}/{label}")

    def chance(self, probability: float) -> bool:
        """Return True with the given probability (one uniform consumed)."""
        return self.random() < probability

    def binomial(self, n: int, p: float) -> int:
        """Number of successes in `n` trials of probability `p`.

        Exact inversion for small means, rounded normal approximation for
        large ones. Always consumes exactly one uniform.
        """
        u = self.random()
        if n <= 0 or p <= 0.0:
            return 0
        if p >= 1.0:
            return n
        if n * min(p, 1.0 - p) > _NORMAL_APPROX_MIN:
            return _binomial_normal(n, p, u)
        if p > 0.5:
            return n - _binomial_inversion(n, 1.0 - p, 1.0 - u)
        return _binomial_inversion(n, p, u)


def _binomial_normal(n: int, p: float, u: float) -> int:
    """Rounded normal approximation, clamped to [0, n]."""
    u = min(max(u, 1e-12), 1.0 - 1e-12)
    z = _STANDARD_NORMAL.inv_cdf(u)
    value = round(n * p + z * math.sqrt(n * p * (1.0 - p)))
    return min(max(value, 0), n)


def _binomial_inversion(n: int, p: float, u: float) -> int:
    """Walk the binomial CDF until it passes `u` (exact, needs small n*p)."""
    q = 1.0 - p
    ratio = p / q
    prob = q**n
    cumulative = prob
    k = 0
    while u > cumulative and k < n:
        k += 1
        prob *= ratio * (n - k + 1) / k
        cumulative += prob
    return k
