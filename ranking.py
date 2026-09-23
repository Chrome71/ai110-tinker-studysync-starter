"""
StudySync -- Find a Study Spot (Ticket 3, Tinker 3B).

Loads study spots from CSV, scores each one against a student profile with
a weighted, explainable score, and returns the top k with their reasons.

Scoring (higher is better):
  noise     within max_noise     +2.0   else -2.0 per level too loud
  distance  within max_distance  +2.0   else -2.0
  seats     at least min_seats   +1.0   else -1.0
  wifi      excellent +0.5, good +0.25, basic +0 (small tie-breaker bonus)
Ties are broken by distance, closest first.
"""

import csv
from pathlib import Path

NOISE_ORDER = {"quiet": 0, "moderate": 1, "loud": 2}
WIFI_BONUS = {"excellent": 0.5, "good": 0.25, "basic": 0.0}

# Resolve the CSV next to this file so the app works from any working directory.
DATA_PATH = Path(__file__).parent / "data" / "study_spots.csv"


def load_study_spots(csv_path: str) -> list:
    """
    Load study spots from a CSV into a list of dicts, converting
    "distance_miles" to float and "seats_available" to int.
    """
    spots = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["distance_miles"] = float(row["distance_miles"])
            row["seats_available"] = int(row["seats_available"])
            spots.append(row)
    return spots


def score_study_spot(profile: dict, spot: dict) -> tuple:
    """
    Score one study spot against a student profile.

    profile example: {"max_noise": "moderate", "max_distance": 1.0, "min_seats": 4}

    Return (score, reasons) where reasons is a list of short strings
    explaining what contributed to the score, e.g. ["quiet enough", "close enough"].
    """
    if profile["max_noise"] not in NOISE_ORDER:
        raise ValueError(f"Unknown max_noise {profile['max_noise']!r}; expected one of {list(NOISE_ORDER)}")
    if spot["noise_level"] not in NOISE_ORDER:
        raise ValueError(f"Unknown noise_level {spot['noise_level']!r} for {spot.get('name')!r}")

    score = 0.0
    reasons = []

    levels_over = NOISE_ORDER[spot["noise_level"]] - NOISE_ORDER[profile["max_noise"]]
    if levels_over <= 0:
        score += 2.0
        reasons.append(f"quiet enough ({spot['noise_level']})")
    else:
        score -= 2.0 * levels_over
        reasons.append(f"too loud ({spot['noise_level']})")

    if spot["distance_miles"] <= profile["max_distance"]:
        score += 2.0
        reasons.append(f"close enough ({spot['distance_miles']} mi)")
    else:
        score -= 2.0
        reasons.append(f"too far ({spot['distance_miles']} mi)")

    if spot["seats_available"] >= profile["min_seats"]:
        score += 1.0
        reasons.append(f"enough seats ({spot['seats_available']})")
    else:
        score -= 1.0
        reasons.append(f"not enough seats ({spot['seats_available']})")

    wifi_bonus = WIFI_BONUS.get(spot.get("wifi_quality"), 0.0)
    if wifi_bonus:
        score += wifi_bonus
        reasons.append(f"{spot['wifi_quality']} wifi")

    return score, reasons


def rank_study_spots(profile: dict, spots: list, k: int = 3) -> list:
    """
    Score every study spot, then return the top k as (spot, score, reasons)
    tuples, sorted by score descending.
    """
    scored = [(spot, *score_study_spot(profile, spot)) for spot in spots]
    # Highest score first; on a tie, the closer spot wins.
    ranked = sorted(scored, key=lambda item: (item[1], -item[0]["distance_miles"]), reverse=True)
    return ranked[:k]


def format_results(ranked: list) -> None:
    """Print each ranked study spot with its score and reasons, one line each."""
    for rank, (spot, score, reasons) in enumerate(ranked, start=1):
        print(f"{rank}. {spot['name']} -- Score: {score:.1f} -- Because: {', '.join(reasons)}")


def render_study_spot_tab():
    import streamlit as st

    st.subheader("Find a Study Spot")
    max_noise = st.selectbox("Max noise level", ["quiet", "moderate", "loud"], index=1)
    max_distance = st.slider("Max distance (miles)", 0.0, 3.0, 1.0)
    min_seats = st.number_input("Minimum seats needed", min_value=1, value=4, step=1)

    if st.button("Find spots"):
        profile = {"max_noise": max_noise, "max_distance": max_distance, "min_seats": min_seats}
        spots = load_study_spots(DATA_PATH)
        ranked = rank_study_spots(profile, spots, k=3)
        for rank, (spot, score, reasons) in enumerate(ranked, start=1):
            st.write(f"{rank}. **{spot['name']}** -- Score: {score:.1f} -- Because: {', '.join(reasons)}")


if __name__ == "__main__":
    spots = load_study_spots(DATA_PATH)
    profile = {"max_noise": "moderate", "max_distance": 1.0, "min_seats": 4}
    ranked = rank_study_spots(profile, spots, k=3)
    format_results(ranked)
