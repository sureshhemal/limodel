"""ValueOutsideTheRange: a reading that cannot happen, judged on its own."""

import pytest

from limodel.analyzer.preprocess.steps.checks.value_outside_the_range import ValueOutsideTheRange


@pytest.fixture
def check():
    """The pH of a tank, as the concentrate inspector sets it up."""
    return ValueOutsideTheRange("ph", "pH", (2.0, 12.0))


def test_it_says_which_value_it_judges(check):
    assert check.field_name == "ph"


def test_a_reading_inside_the_range_is_accepted(check, readings):
    assert check.find(readings(ph=(5.9, 4.3, 4.5))) is None


def test_a_reading_below_the_range_is_rejected(check, readings):
    given = readings(ph=(5.9, 0.072, 4.5))

    reading, field_name, reason = check.find(given)

    assert reading is given[1]
    assert field_name == "ph"
    assert reason == "pH 0.072 is outside 2 to 12"


def test_a_reading_above_the_range_is_rejected(check, readings):
    given = readings(ph=(5.9, 13.4, 4.5))

    reading, _, _ = check.find(given)

    assert reading is given[1]


def test_the_edges_of_the_range_are_allowed(check, readings):
    assert check.find(readings(ph=(2.0, 12.0, 7.0))) is None


def test_it_names_the_earliest_of_several(check, readings):
    given = readings(ph=(0.5, 5.9, 0.8))

    reading, _, _ = check.find(given)

    assert reading is given[0]


def test_readings_without_the_value_are_passed_over(check, readings):
    assert check.find(readings(ph=(None, 5.9, 4.5))) is None


def test_a_single_reading_can_still_be_rejected(check, readings):
    """Nothing to compare with, and nothing needed: the value is wrong by itself."""
    given = readings(ph=(0.072,))

    reading, _, _ = check.find(given)

    assert reading is given[0]


def test_it_serves_the_temperature_too(readings):
    check = ValueOutsideTheRange("temp_c", "temperature", (5.0, 40.0))
    given = readings(temp_c=(21.4, 95.0))

    reading, field_name, reason = check.find(given)

    assert reading is given[1]
    assert field_name == "temp_c"
    assert reason == "temperature 95 is outside 5 to 40"


def test_it_changes_nothing(check, readings):
    given = readings(ph=(5.9, 0.072, 4.5))

    check.find(given)

    assert [reading.ph for reading in given] == [5.9, 0.072, 4.5]
