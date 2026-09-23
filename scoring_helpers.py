"""
Shared scoring helpers for StudySync.

apply_streak_bonus() was moved here from scoring.py during Tinker 1B, Part 2.
"""


def apply_streak_bonus(combined_score: int, streak_days: int) -> int:
    """Add a bonus for consecutive study days, capped at 100."""
    if streak_days < 0:
        raise ValueError(f"streak_days can't be negative, got {streak_days}")
    boosted = combined_score + streak_days * 2
    return min(boosted, 100)
