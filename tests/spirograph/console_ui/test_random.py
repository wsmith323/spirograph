import pytest

from spirograph.console_ui import random as random_helpers
from spirograph.console_ui.types import RandomConstraintMode, RandomEvolutionMode


def _return_upper_bound(_lower: int, upper: int) -> int:
    return upper


def test_random_pen_offset_physical_mode_caps_at_rolling_radius(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(random_helpers.random, 'randint', _return_upper_bound)

    result = random_helpers.random_pen_offset(
        rolling_radius=45,
        prev=None,
        constraint=RandomConstraintMode.PHYSICAL,
        evolution=RandomEvolutionMode.RANDOM,
    )

    assert result == 45
    assert result <= 45


def test_random_pen_offset_extended_mode_can_exceed_rolling_radius(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(random_helpers.random, 'randint', _return_upper_bound)

    result = random_helpers.random_pen_offset(
        rolling_radius=45,
        prev=None,
        constraint=RandomConstraintMode.EXTENDED,
        evolution=RandomEvolutionMode.RANDOM,
    )

    assert result > 45


def test_random_pen_offset_wild_mode_is_at_least_as_permissive_as_extended(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(random_helpers.random, 'randint', _return_upper_bound)

    extended_result = random_helpers.random_pen_offset(
        rolling_radius=45,
        prev=None,
        constraint=RandomConstraintMode.EXTENDED,
        evolution=RandomEvolutionMode.RANDOM,
    )
    wild_result = random_helpers.random_pen_offset(
        rolling_radius=45,
        prev=None,
        constraint=RandomConstraintMode.WILD,
        evolution=RandomEvolutionMode.RANDOM,
    )

    assert wild_result >= extended_result


def test_random_pen_offset_physical_mode_handles_small_rolling_radius(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(random_helpers.random, 'randint', _return_upper_bound)

    result = random_helpers.random_pen_offset(
        rolling_radius=1,
        prev=None,
        constraint=RandomConstraintMode.PHYSICAL,
        evolution=RandomEvolutionMode.RANDOM,
    )

    assert result == 1
