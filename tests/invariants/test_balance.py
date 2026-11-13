"""Balance (SDD 11): no card dominates the top-scoring runs of 1,000 random-policy games.

"Top" = best 10% by public health score. A card's share is its share of all
cards played in those runs; no card may exceed 25%. Family shares are reported
with their share in all runs for comparison (families differ in size).
"""

from collections import Counter

from tests.conftest import write_report
from tools.experiments import load_content, pmap
from tools.experiments_ripple import balance_worker

SEEDS = 250  # x 4 policies = 1,000 runs
LIMIT = 0.25


def test_no_card_dominates_top_runs() -> None:
    rows = [row for group in pmap(balance_worker, [f"bal-{i}" for i in range(SEEDS)])
            for row in group]
    rows.sort(key=lambda row: (-row["score"], row["seed"], row["policy"]))
    top = rows[: len(rows) // 10]
    families = {card.id: card.family for card in load_content().cards.values()}
    top_cards = Counter(card for row in top for card in row["cards"])
    all_cards = Counter(card for row in rows for card in row["cards"])
    top_total, all_total = sum(top_cards.values()), sum(all_cards.values())
    card_share = {card: round(top_cards[card] / top_total, 3) for card in sorted(families)}
    family_top = Counter({f: 0 for f in families.values()})
    family_all = Counter({f: 0 for f in families.values()})
    for card, family in families.items():
        family_top[family] += top_cards[card]
        family_all[family] += all_cards[card]
    scores = sorted(row["score"] for row in rows)
    report = {
        "runs": len(rows), "top_runs": len(top), "limit": LIMIT,
        "max_card_share_in_top": max(card_share.values()),
        "card_share_in_top": card_share,
        "family_share_in_top": {f: round(family_top[f] / top_total, 3)
                                for f in sorted(family_top)},
        "family_share_in_all": {f: round(family_all[f] / all_total, 3)
                                for f in sorted(family_all)},
        "score_quantiles": {"p10": scores[len(scores) // 10], "p50": scores[len(scores) // 2],
                            "p90": scores[9 * len(scores) // 10], "min": scores[0],
                            "max": scores[-1]},
    }
    write_report("balance", report)
    assert len(rows) == 1000
    assert max(card_share.values()) <= LIMIT
