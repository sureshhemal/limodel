"""ValueMovingTooFast: a change judged by how long it had to happen in."""

import pytest

from limodel.analyzer.preprocess.steps.checks.value_moving_too_fast import ValueMovingTooFast


@pytest.fixture
def check():
    """The pH of a tank, as the concentrate inspector sets it up: 1.5 in 15 minutes."""
    return ValueMovingTooFast("ph", "pH", allowance=1.5, over_minutes=15.0)


def test_it_says_which_value_it_judges(check):
    assert check.field_name == "ph"


def test_a_slow_change_is_accepted(check, readings):
    assert check.find_worst_offender(readings(ph=(5.9, 5.85, 5.8))) is None


def test_a_change_inside_the_allowance_is_accepted(check, readings):
    """1.0 in 15 minutes, against 1.5 allowed."""
    assert check.find_worst_offender(readings(ph=(5.9, 4.9, 4.85))) is None


def test_a_change_over_the_allowance_is_rejected(check, readings):
    given = readings(ph=(5.9, 4.1, 5.85))

    reading, field_name, reason = check.find_worst_offender(given)

    assert reading is given[1]
    assert field_name == "ph"
    assert reason == "pH moved 1.8 in 15 minutes, more than 1.5 in 15"


def test_the_same_change_over_longer_is_accepted(check, readings):
    """Too fast across 15 minutes, ordinary drift across four hours."""
    assert check.find_worst_offender(readings(ph=(5.9, 4.1, 4.05), minutes=(0, 240, 480))) is None


def test_it_rejects_the_reading_further_from_the_usual(check, readings):
    """The series sits near 5.9, so the 4.0 at the start is the stranger."""
    given = readings(ph=(4.0, 5.9, 5.95))

    reading, _, _ = check.find_worst_offender(given)

    assert reading is given[0]


def test_it_takes_the_fastest_change_when_there_are_several(check, readings):
    given = readings(ph=(5.9, 4.1, 5.85, 2.5))

    reading, _, _ = check.find_worst_offender(given)

    assert reading is given[3]


def test_one_reading_cannot_be_judged(check, readings):
    assert check.find_worst_offender(readings(ph=(0.072,))) is None


def test_readings_without_the_value_are_passed_over(check, readings):
    assert check.find_worst_offender(readings(ph=(None, 5.9, None))) is None


def test_the_allowance_it_is_given_decides(readings):
    """A change of 1.0 passes at 1.5 allowed and fails at 0.5. The series sits near 4.9,
    so the 5.9 at the start is the one rejected."""
    given = readings(ph=(5.9, 4.9, 4.85))
    strict = ValueMovingTooFast("ph", "pH", allowance=0.5, over_minutes=15.0)

    assert ValueMovingTooFast("ph", "pH", 1.5, 15.0).find_worst_offender(given) is None
    assert strict.find_worst_offender(given)[0] is given[0]


def test_it_serves_the_temperature_too(readings):
    check = ValueMovingTooFast("temp_c", "temperature", allowance=2.0, over_minutes=15.0)
    given = readings(temp_c=(21.4, 28.0, 21.5))

    reading, field_name, reason = check.find_worst_offender(given)

    assert reading is given[1]
    assert field_name == "temp_c"
    assert reason == "temperature moved 6.6 in 15 minutes, more than 2 in 15"


def test_it_changes_nothing(check, readings):
    given = readings(ph=(5.9, 4.1, 5.85))

    check.find_worst_offender(given)

    assert [reading.ph for reading in given] == [5.9, 4.1, 5.85]
