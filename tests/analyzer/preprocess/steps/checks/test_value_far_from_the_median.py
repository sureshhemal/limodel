"""ValueFarFromTheMedian: the one reading that is nothing like the rest of its series."""

import pytest

from limodel.analyzer.preprocess.steps.checks.value_far_from_the_median import ValueFarFromTheMedian


@pytest.fixture
def check():
    """The weights of a tank, as the concentrate inspector sets it up."""
    return ValueFarFromTheMedian("weight_g", "weight", "g", share=0.10, fewest=3)


def test_it_says_which_value_it_judges(check):
    assert check.field_name == "weight_g"


def test_values_near_their_median_are_accepted(check, readings):
    assert check.find(readings(weight_g=(2119.7, 2117.8, 2100.0))) is None


def test_the_value_furthest_from_the_median_is_rejected(check, readings):
    given = readings(weight_g=(2119.7, 2117.8, 1800.0))

    reading, field_name, reason = check.find(given)

    assert reading is given[2]
    assert field_name == "weight_g"
    assert reason == "weight 1800 g is 317.8 g away from the usual 2117.8 g"


def test_a_bad_first_reading_is_rejected_not_its_neighbour(check, readings):
    """Judged against its neighbour, the good second reading would be blamed instead."""
    given = readings(weight_g=(209.7, 2098.9, 2088.9, 2079.5))

    reading, _, _ = check.find(given)

    assert reading is given[0]


def test_too_few_readings_cannot_be_judged(check, readings):
    """With two, the median is their midpoint and each sits as far from it as the other."""
    assert check.find(readings(weight_g=(209.7, 2098.9))) is None


def test_no_readings_at_all_is_not_an_error(check):
    assert check.find([]) is None


def test_readings_without_the_value_are_passed_over(check, readings):
    assert check.find(readings(weight_g=(2119.7, None, 2117.8, 2100.0))) is None


def test_the_share_it_is_given_decides(readings):
    given = readings(weight_g=(2119.7, 2117.8, 2100.0))
    strict = ValueFarFromTheMedian("weight_g", "weight", "g", share=0.001, fewest=3)

    reading, _, _ = strict.find(given)

    assert reading is given[2]


def test_it_serves_any_value_that_holds_one_level(power_readings):
    """The same rule, set up for the current the supply holds steady."""
    check = ValueFarFromTheMedian("supply_current_a", "the supply current", "A", 0.10, 3)
    given = power_readings(supply_current_a=(0.045, 0.045, 0.46, 0.045))

    reading, field_name, reason = check.find(given)

    assert reading is given[2]
    assert field_name == "supply_current_a"
    assert reason == "the supply current 0.46 A is 0.415 A away from the usual 0.045 A"


def test_it_changes_nothing(check, readings):
    given = readings(weight_g=(2119.7, 2117.8, 1800.0))

    check.find(given)

    assert [reading.weight_g for reading in given] == [2119.7, 2117.8, 1800.0]
