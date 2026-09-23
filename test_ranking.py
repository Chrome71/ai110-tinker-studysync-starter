"""
Tinker 3B tests for ranking.py.
"""

import pytest

from ranking import (
    DATA_PATH,
    format_results,
    load_study_spots,
    rank_study_spots,
    score_study_spot,
)

DEFAULT_PROFILE = {"max_noise": "moderate", "max_distance": 1.0, "min_seats": 4}


def make_spot(name="Spot", noise="quiet", distance=0.5, seats=10, wifi="basic"):
    return {
        "name": name,
        "noise_level": noise,
        "distance_miles": distance,
        "seats_available": seats,
        "wifi_quality": wifi,
    }


# Loading
def test_load_study_spots_converts_types():
    spots = load_study_spots(DATA_PATH)
    assert len(spots) == 10
    first = spots[0]
    assert first["name"] == "Innovation Commons"
    assert first["distance_miles"] == 0.3 and isinstance(first["distance_miles"], float)
    assert first["seats_available"] == 12 and isinstance(first["seats_available"], int)


def test_load_study_spots_from_custom_file(tmp_path):
    path = tmp_path / "spots.csv"
    path.write_text(
        "id,name,noise_level,distance_miles,wifi_quality,seats_available\n"
        "1,Tiny Room,quiet,1,good,2\n"
    )
    assert load_study_spots(path) == [
        {
            "id": "1",
            "name": "Tiny Room",
            "noise_level": "quiet",
            "distance_miles": 1.0,
            "wifi_quality": "good",
            "seats_available": 2,
        }
    ]


def test_load_study_spots_header_only_is_empty(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("id,name,noise_level,distance_miles,wifi_quality,seats_available\n")
    assert load_study_spots(path) == []


# Scoring
def test_score_perfect_match():
    score, reasons = score_study_spot(DEFAULT_PROFILE, make_spot(wifi="excellent"))
    assert score == 5.5
    assert reasons == ["quiet enough (quiet)", "close enough (0.5 mi)", "enough seats (10)", "excellent wifi"]


def test_score_boundaries_count_as_ok():
    # Exactly at max noise, max distance and min seats should all pass.
    spot = make_spot(noise="moderate", distance=1.0, seats=4)
    score, reasons = score_study_spot(DEFAULT_PROFILE, spot)
    assert score == 5.0
    assert "quiet enough (moderate)" in reasons
    assert "close enough (1.0 mi)" in reasons
    assert "enough seats (4)" in reasons


def test_score_every_factor_can_hurt():
    profile = {"max_noise": "quiet", "max_distance": 0.5, "min_seats": 20}
    score, reasons = score_study_spot(profile, make_spot(noise="loud", distance=2.0, seats=5))
    assert score == -4.0 - 2.0 - 1.0
    assert reasons == ["too loud (loud)", "too far (2.0 mi)", "not enough seats (5)"]


def test_score_louder_is_worse():
    profile = {"max_noise": "quiet", "max_distance": 1.0, "min_seats": 1}
    moderate, _ = score_study_spot(profile, make_spot(noise="moderate"))
    loud, _ = score_study_spot(profile, make_spot(noise="loud"))
    assert loud < moderate


def test_score_rejects_unknown_noise():
    with pytest.raises(ValueError):
        score_study_spot({**DEFAULT_PROFILE, "max_noise": "silent"}, make_spot())
    with pytest.raises(ValueError):
        score_study_spot(DEFAULT_PROFILE, make_spot(noise="deafening"))


# Ranking
def test_rank_sorted_descending_and_limited_to_k():
    spots = load_study_spots(DATA_PATH)
    ranked = rank_study_spots(DEFAULT_PROFILE, spots, k=3)
    assert len(ranked) == 3
    scores = [score for _, score, _ in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_default_profile_top_three():
    ranked = rank_study_spots(DEFAULT_PROFILE, load_study_spots(DATA_PATH), k=3)
    assert [spot["name"] for spot, _, _ in ranked] == [
        "Innovation Commons",
        "Group Project Room B",
        "Engineering Lounge",
    ]


def test_rank_excludes_loud_and_far_spots_from_top_five():
    ranked = rank_study_spots(DEFAULT_PROFILE, load_study_spots(DATA_PATH), k=5)
    names = {spot["name"] for spot, _, _ in ranked}
    assert names.isdisjoint({"Courtyard Cafe", "Student Union Tables", "Rooftop Study Deck", "24-Hour Annex"})


def test_rank_tie_goes_to_closer_spot():
    far = make_spot("Far", distance=0.9)
    near = make_spot("Near", distance=0.2)
    ranked = rank_study_spots(DEFAULT_PROFILE, [far, near], k=2)
    assert [spot["name"] for spot, _, _ in ranked] == ["Near", "Far"]


def test_rank_k_larger_than_list_and_empty_list():
    spots = [make_spot("A"), make_spot("B")]
    assert len(rank_study_spots(DEFAULT_PROFILE, spots, k=10)) == 2
    assert rank_study_spots(DEFAULT_PROFILE, [], k=3) == []


# Output
def test_format_results_prints_one_numbered_line_each(capsys):
    ranked = [(make_spot("Alpha"), 5.0, ["quiet enough", "close enough"]), (make_spot("Beta"), 3.25, ["too far"])]
    format_results(ranked)
    assert capsys.readouterr().out.splitlines() == [
        "1. Alpha -- Score: 5.0 -- Because: quiet enough, close enough",
        "2. Beta -- Score: 3.2 -- Because: too far",
    ]


# The running app (skipped if Streamlit isn't installed)
def test_study_spot_tab_shows_top_three():
    testing = pytest.importorskip("streamlit.testing.v1")
    at = testing.AppTest.from_file("app.py", default_timeout=30).run()
    next(b for b in at.button if b.label == "Find spots").click().run()
    assert not at.exception
    assert not at.warning
    lines = [m.value for m in at.markdown if " -- Score: " in m.value]
    assert len(lines) == 3
    assert lines[0].startswith("1. **Innovation Commons** -- Score: 5.5")
