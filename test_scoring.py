"""
Tinker 1B tests for session_rating() and apply_streak_bonus().
"""

import pytest

from scoring import session_rating
from scoring_helpers import apply_streak_bonus


def test_session_rating_boundary_90_is_great():
    assert session_rating(90) == "Great"


@pytest.mark.parametrize(
    "score, expected",
    [
        (100, "Great"),
        (89, "Good"),
        (80, "Good"),
        (79, "OK"),
        (70, "OK"),
        (69, "Meh"),
        (60, "Meh"),
        (59, "Skip"),
        (0, "Skip"),
    ],
)
def test_session_rating_boundaries(score, expected):
    assert session_rating(score) == expected


def test_session_rating_accepts_float():
    assert session_rating(89.5) == "Good"


# Breaker inputs
@pytest.mark.parametrize("bad", ["90", None, True])
def test_session_rating_rejects_non_numbers(bad):
    with pytest.raises(TypeError):
        session_rating(bad)


def test_session_rating_rejects_nan():
    with pytest.raises(ValueError):
        session_rating(float("nan"))


def test_session_rating_rejects_negative():
    with pytest.raises(ValueError):
        session_rating(-5)


def test_apply_streak_bonus_adds_two_per_day():
    assert apply_streak_bonus(70, 3) == 76


def test_apply_streak_bonus_caps_at_100():
    assert apply_streak_bonus(95, 10) == 100
    assert apply_streak_bonus(120, 0) == 100


def test_apply_streak_bonus_rejects_negative_streak():
    with pytest.raises(ValueError):
        apply_streak_bonus(50, -10)


def test_streak_bonus_still_importable_from_scoring():
    # The Session Scorer tab and run_demo() use this name via scoring.py.
    import scoring

    assert scoring.apply_streak_bonus is apply_streak_bonus
