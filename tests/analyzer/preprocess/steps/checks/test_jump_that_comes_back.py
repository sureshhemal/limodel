"""JumpThatComesBack: a reading that jumps away and is put straight back."""

import pytest

from limodel.analyzer.preprocess.steps.checks.jump_that_comes_back import JumpThatComesBack


@pytest.fixture
def check():
    """The conductivity of a tank, as the tank inspectors set it up."""
    return JumpThatComesBack("conductivity_us_cm", "conductivity",
                             smallest_jump_share=0.10, comes_back_share=0.7)


def test_it_says_which_value_it_judges(check):
    assert check.field_name == "conductivity_us_cm"


def test_a_series_that_climbs_steadily_is_accepted(check, readings):
    """Conductivity is meant to climb all run, so climbing is not a fault."""
    given = readings(conductivity_us_cm=(1673.0, 3554.0, 4652.4, 5095.9, 6200.0))

    assert check.find_worst_offender(given) is None


def test_a_jump_that_stays_is_accepted(check, readings):
    """A real change of level does not come back. Only half of this one does."""
    given = readings(conductivity_us_cm=(17720.9, 7610.0, 12500.0))

    assert check.find_worst_offender(given) is None


def test_a_jump_that_comes_back_is_rejected(check, readings):
    given = readings(conductivity_us_cm=(17720.9, 7610.0, 17495.0))

    reading, field_name, reason = check.find_worst_offender(given)

    assert reading is given[1]
    assert field_name == "conductivity_us_cm"
    assert reason == "conductivity jumped to 7610 and the next reading put 98% of it back"


def test_a_jump_upwards_is_rejected_the_same_way(check, readings):
    given = readings(conductivity_us_cm=(17549.7, 173997.1, 17307.2))

    reading, _, _ = check.find_worst_offender(given)

    assert reading is given[1]


def test_a_wobble_too_small_to_matter_is_accepted(check, readings):
    """It comes back, but 500 on a series reading 105,000 is not a digit written wrong."""
    given = readings(conductivity_us_cm=(105627.0, 106128.0, 105432.0))

    assert check.find_worst_offender(given) is None


def test_it_names_the_reading_in_the_middle_of_the_jump(check, readings):
    given = readings(conductivity_us_cm=(16566.7, 16500.0, 6471.3, 16354.6, 16300.0))

    reading, _, _ = check.find_worst_offender(given)

    assert reading is given[2]


def test_two_readings_cannot_be_judged(check, readings):
    """A jump needs a reading before it and a reading after it."""
    assert check.find_worst_offender(readings(conductivity_us_cm=(17720.9, 7610.0))) is None


def test_the_last_reading_cannot_be_judged(check, readings):
    """Nothing follows it, so nothing can put the jump back."""
    given = readings(conductivity_us_cm=(17720.9, 17700.0, 7610.0))

    assert check.find_worst_offender(given) is None


def test_readings_without_the_value_are_passed_over(check, readings):
    given = readings(conductivity_us_cm=(17720.9, None, 7610.0, 17495.0))

    reading, _, _ = check.find_worst_offender(given)

    assert reading is given[2]


def test_how_much_has_to_come_back_is_given_to_it(readings):
    """A jump that only half returns passes at 0.7 and fails at 0.4."""
    given = readings(conductivity_us_cm=(17720.9, 7610.0, 12500.0))
    forgiving = JumpThatComesBack("conductivity_us_cm", "conductivity", 0.10, 0.4)

    assert forgiving.find_worst_offender(given)[0] is given[1]


def test_it_changes_nothing(check, readings):
    given = readings(conductivity_us_cm=(17720.9, 7610.0, 17495.0))

    check.find_worst_offender(given)

    assert [reading.conductivity_us_cm for reading in given] == [17720.9, 7610.0, 17495.0]
