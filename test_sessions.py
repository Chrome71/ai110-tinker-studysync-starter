"""
Tinker 2B tests for sessions.py.
"""

from dataclasses import is_dataclass
from datetime import date

import pytest

from sessions import (
    PlainSession,
    SessionDC,
    find_conflicts,
    next_occurrence,
    validate_session,
)


# Part 2: input validation
def test_validate_session_accepts_good_input():
    assert validate_session("Calc II", 30) == []


@pytest.mark.parametrize("subject", ["", "   ", "\t\n", None])
def test_validate_session_rejects_empty_subject(subject):
    assert validate_session(subject, 30) == ["Subject can't be empty."]


@pytest.mark.parametrize("duration", [0, -5, -0.5, "30", None, True])
def test_validate_session_rejects_bad_duration(duration):
    assert validate_session("Calc II", duration) == ["Duration must be greater than 0 minutes."]


def test_validate_session_reports_both_errors():
    assert len(validate_session("  ", 0)) == 2


# Part 3: dataclass
def test_session_dc_is_a_dataclass_matching_plain_session():
    dc = SessionDC("Calc II", 45)
    plain = PlainSession("Calc II", 45)
    assert is_dataclass(dc)
    assert (dc.subject, dc.minutes, dc.priority) == (plain.subject, plain.minutes, plain.priority)
    assert dc.priority == "medium"


def test_session_dc_repr_and_equality():
    dc = SessionDC("Calc II", 45, priority="high")
    assert repr(dc) == "SessionDC(subject='Calc II', minutes=45, priority='high')"
    assert dc == SessionDC("Calc II", 45, priority="high")


# Part 4: recurring dates
def test_next_occurrence_daily():
    assert next_occurrence(date(2026, 1, 1), "daily") == date(2026, 1, 2)


def test_next_occurrence_weekly():
    assert next_occurrence(date(2026, 1, 1), "weekly") == date(2026, 1, 8)


def test_next_occurrence_crosses_month_and_leap_day():
    assert next_occurrence(date(2028, 2, 28), "daily") == date(2028, 2, 29)
    assert next_occurrence(date(2026, 12, 28), "weekly") == date(2027, 1, 4)


def test_next_occurrence_rejects_unknown_frequency():
    with pytest.raises(ValueError):
        next_occurrence(date(2026, 1, 1), "monthly")


# Part 4: conflicts
def test_find_conflicts_empty_list():
    assert find_conflicts([]) == []


def test_find_conflicts_none_found():
    assert find_conflicts([{"subject": "A", "slot": "08:00"}, {"subject": "B", "slot": "09:00"}]) == []


def test_find_conflicts_single_pair():
    calc = {"subject": "Calc II", "slot": "08:00"}
    chem = {"subject": "Chem Lab", "slot": "08:00"}
    history = {"subject": "History", "slot": "09:00"}
    assert find_conflicts([calc, chem, history]) == [(calc, chem)]


def test_find_conflicts_three_in_one_slot_gives_every_pair_once():
    a, b, c = ({"subject": s, "slot": "10:00"} for s in "ABC")
    assert find_conflicts([a, b, c]) == [(a, b), (a, c), (b, c)]


# Parts 1-2 in the running app (skipped if Streamlit isn't installed)
@pytest.fixture
def app():
    testing = pytest.importorskip("streamlit.testing.v1")
    at = testing.AppTest.from_file("app.py", default_timeout=30).run()
    assert not at.exception
    return at


def _button(at, label):
    return next(b for b in at.button if b.label == label)


def _metric(at, label):
    return next(m for m in at.metric if m.label == label)


def test_fixed_counter_survives_reruns(app):
    for _ in range(3):
        _button(app, "Log a session (fixed)").click().run()
    assert _metric(app, "Sessions logged (fixed)").value == "3"


def test_add_session_rejects_empty_subject(app):
    app.text_input[0].set_value("   ")
    _button(app, "Add session").click().run()
    assert [e.value for e in app.error] == ["Subject can't be empty."]
    assert app.session_state.mini_sessions == []


def test_add_session_rejects_zero_duration(app):
    app.text_input[0].set_value("Calc II")
    next(n for n in app.number_input if n.label == "Duration (minutes)").set_value(0)
    _button(app, "Add session").click().run()
    assert [e.value for e in app.error] == ["Duration must be greater than 0 minutes."]
    assert app.session_state.mini_sessions == []


def test_add_session_accepts_valid_input(app):
    app.text_input[0].set_value("  Calc II  ")
    _button(app, "Add session").click().run()
    assert not app.error
    assert app.session_state.mini_sessions == [{"subject": "Calc II", "duration": 30}]
