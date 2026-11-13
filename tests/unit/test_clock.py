"""Clock: turn boundaries."""

from engine.core.clock import Clock


def test_default_turn_starts() -> None:
    clock = Clock()
    assert [clock.turn_start(turn) for turn in range(7)] == [0, 8, 17, 26, 34, 43, 52]


def test_turn_of_and_is_turn_start() -> None:
    clock = Clock()
    assert clock.turn_of(0) == 0
    assert clock.turn_of(7) == 0
    assert clock.turn_of(8) == 1
    assert clock.turn_of(51) == 5
    assert clock.is_turn_start(17) and not clock.is_turn_start(18)
