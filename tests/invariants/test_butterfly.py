"""Butterfly (SDD 11): ripple size over 500 seeds is heavy tailed; a no-op is zero.

Ripple size = number of events that exist in exactly one of the two runs
(player versus baseline) after ONE random card. "Large" = at least LARGE events.
The build prompt asks that about 1 in 6 actions gives a large ripple.
"""

from collections import Counter

from tests.conftest import write_report
from tools.experiments import pmap
from tools.experiments_ripple import butterfly_worker

SEEDS = 500
LARGE = 10


def quantile(ordered: list[int], q: float) -> int:
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


def test_ripple_distribution_is_heavy_tailed() -> None:
    rows = pmap(butterfly_worker, [f"fly-{i}" for i in range(SEEDS)])
    sizes = sorted(row["ripple_size"] for row in rows)
    mean = sum(sizes) / SEEDS
    large_share = sum(1 for size in sizes if size >= LARGE) / SEEDS
    played = Counter(row["card"] for row in rows)
    large_by_card = Counter(row["card"] for row in rows if row["ripple_size"] >= LARGE)
    report = {
        "seeds": SEEDS, "large_means_at_least": LARGE,
        "quantiles": {name: quantile(sizes, q) for name, q in
                      [("p50", 0.5), ("p75", 0.75), ("p90", 0.9), ("p95", 0.95), ("p99", 0.99)]},
        "max": sizes[-1], "mean": round(mean, 2),
        "share_zero": round(sizes.count(0) / SEEDS, 3),
        "share_large": round(large_share, 3),
        "top_1_percent_share_of_total": round(sum(sizes[-SEEDS // 100:]) / max(1, sum(sizes)), 3),
        "large_share_by_card": {card: round(large_by_card[card] / played[card], 2)
                                for card in sorted(played)},
    }
    write_report("butterfly", report)
    median = quantile(sizes, 0.5)
    assert mean > 1.5 * max(1, median)  # mean far above median: a long right tail
    assert quantile(sizes, 0.99) >= 5 * max(1, quantile(sizes, 0.75))
    assert 0.10 <= large_share <= 0.25  # about 1 in 6
