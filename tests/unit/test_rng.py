"""RNG: reproducible, forkable, binomial sampler behaves."""

from engine.core.rng import Rng


def test_same_seed_same_numbers() -> None:
    assert [Rng("a").random() for _ in range(3)] == [Rng("a").random() for _ in range(3)]
    assert Rng("a").random() != Rng("b").random()


def test_fork_does_not_consume_parent() -> None:
    parent, twin = Rng("seed"), Rng("seed")
    parent.fork("child").random()
    assert parent.random() == twin.random()


def test_fork_depends_only_on_labels() -> None:
    assert Rng("s").fork("x").fork("y").random() == Rng("s/x/y").random()
    assert Rng("s").fork("x").random() != Rng("s").fork("y").random()


def test_binomial_edges_and_one_uniform_per_call() -> None:
    rng, twin = Rng("b"), Rng("b")
    assert rng.binomial(0, 0.5) == 0
    assert rng.binomial(10, 0.0) == 0
    assert rng.binomial(10, 1.0) == 10
    for _ in range(3):
        twin.random()
    assert rng.random() == twin.random()


def test_binomial_mean_and_range() -> None:
    for n, p in [(20, 0.1), (20, 0.9), (400, 0.02), (5000, 0.3), (5000, 0.999)]:
        rng = Rng(f"mean:{n}:{p}")
        draws = [rng.binomial(n, p) for _ in range(4000)]
        assert all(0 <= value <= n for value in draws)
        mean = sum(draws) / len(draws)
        sd = (n * p * (1 - p)) ** 0.5
        assert abs(mean - n * p) < 0.1 * sd + 0.05


def test_binomial_is_monotone_in_p_for_the_same_stream() -> None:
    for label in range(50):
        low = Rng(f"m{label}").binomial(200, 0.05)
        high = Rng(f"m{label}").binomial(200, 0.06)
        assert high >= low
