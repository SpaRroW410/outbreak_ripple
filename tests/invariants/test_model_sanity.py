"""Model sanity (SDD 11): epidemic threshold near R0 = 1, herd immunity near 1 - 1/R0."""

from tests.conftest import write_report
from tools.model_sanity import epidemic_threshold, herd_immunity_threshold


def test_epidemic_threshold_is_near_r0_of_one() -> None:
    result = epidemic_threshold()
    write_report("sanity_epidemic_threshold", result)
    attack = dict(zip(result["r0_grid"], result["mean_attack_rate"], strict=True))  # type: ignore[call-overload]
    assert attack[0.8] < 0.01
    assert attack[1.5] > 0.30
    assert 0.9 <= result["measured_threshold_r0"] <= 1.15  # type: ignore[operator]


def test_herd_immunity_threshold_is_near_one_minus_one_over_r0() -> None:
    results = [herd_immunity_threshold(r0) for r0 in (2.0, 3.0, 4.0)]
    write_report("sanity_herd_immunity", {"results": results})
    for result in results:
        assert abs(result["measured_threshold"] - result["expected"]) < 0.05  # type: ignore[operator]
