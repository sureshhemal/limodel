"""CurrentDensity: the run's usual current spread over the membrane area."""

import pytest

from limodel.analyzer.calculate.quantities.current_density import CurrentDensity


@pytest.fixture
def half_an_amp_with_one_spike(a_stack_reading):
    """A median of 0.5 A, where the mean would be pulled up to 0.9167 A by the spike."""
    return (a_stack_reading(minute=0, supply_current_a=0.25),
            a_stack_reading(minute=30, supply_current_a=0.5),
            a_stack_reading(minute=60, supply_current_a=2.0))


def test_it_finds_the_density_of_the_current_the_run_held(a_run, a_stack_reading):
    """0.5 A is 500 mA, and over 10 cm2 that is 50 mA/cm2."""
    run = a_run(area_cm2=10.0,
                stack_readings=(a_stack_reading(minute=0, supply_current_a=0.5),
                                a_stack_reading(minute=60, supply_current_a=0.5)))

    assert CurrentDensity.find_ma_per_cm2(run) == 50.0


def test_one_wild_minute_does_not_move_it(a_run, half_an_amp_with_one_spike):
    """On the mean the same log would read 91.67 mA/cm2, which no minute of it ran at."""
    run = a_run(area_cm2=10.0, stack_readings=half_an_amp_with_one_spike)

    assert CurrentDensity.find_ma_per_cm2(run) == 50.0


def test_an_even_number_of_minutes_takes_their_midpoint(a_run, a_stack_reading):
    """0.25 A and 0.75 A give 0.5 A, so 50 mA/cm2 again."""
    run = a_run(area_cm2=10.0,
                stack_readings=(a_stack_reading(minute=0, supply_current_a=0.25),
                                a_stack_reading(minute=60, supply_current_a=0.75)))

    assert CurrentDensity.find_ma_per_cm2(run) == 50.0


def test_a_smaller_area_carries_a_denser_current(a_run, half_an_amp_with_one_spike):
    """The same 500 mA over 5 cm2 is 100 mA/cm2."""
    run = a_run(area_cm2=5.0, stack_readings=half_an_amp_with_one_spike)

    assert CurrentDensity.find_ma_per_cm2(run) == 100.0


def test_a_minute_without_a_current_is_passed_over(a_run, a_stack_reading):
    """Counted as a reading, the blank would sit in the middle and become the median."""
    run = a_run(area_cm2=10.0,
                stack_readings=(a_stack_reading(minute=0, supply_current_a=0.5),
                                a_stack_reading(minute=30, supply_current_a=None),
                                a_stack_reading(minute=60, supply_current_a=0.5)))

    assert CurrentDensity.find_ma_per_cm2(run) == 50.0


def test_one_minute_of_the_log_is_its_own_median(a_run, a_stack_reading):
    run = a_run(area_cm2=10.0,
                stack_readings=(a_stack_reading(minute=0, supply_current_a=0.5),))

    assert CurrentDensity.find_ma_per_cm2(run) == 50.0


def test_a_log_that_recorded_no_current_at_all_gives_nothing(a_run, a_stack_reading):
    run = a_run(stack_readings=(a_stack_reading(minute=0, supply_current_a=None),))

    assert CurrentDensity.find_ma_per_cm2(run) is None


def test_a_run_with_no_power_log_at_all_is_not_an_error(a_run):
    assert CurrentDensity.find_ma_per_cm2(a_run()) is None


def test_no_area_cannot_be_divided_into(a_run, half_an_amp_with_one_spike):
    run = a_run(area_cm2=0.0, stack_readings=half_an_amp_with_one_spike)

    assert CurrentDensity.find_ma_per_cm2(run) is None


def test_it_changes_nothing(a_run, half_an_amp_with_one_spike):
    run = a_run(stack_readings=half_an_amp_with_one_spike)

    CurrentDensity.find_ma_per_cm2(run)

    assert [reading.supply_current_a for reading in run.stack_readings] == [0.25, 0.5, 2.0]
