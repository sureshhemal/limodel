"""StackVoltage: the highest volts a run reached and the volts it began at."""

import pytest

from limodel.analyzer.calculate.quantities.stack_voltage import StackVoltage


@pytest.fixture
def a_rising_then_easing_log(a_stack_reading):
    """5 V at the start, 12 V at the peak, 8 V by the end."""
    return (a_stack_reading(minute=0, supply_voltage_v=5.0),
            a_stack_reading(minute=30, supply_voltage_v=12.0),
            a_stack_reading(minute=60, supply_voltage_v=8.0))


def test_it_finds_the_highest_volts_of_the_run(a_run, a_rising_then_easing_log):
    run = a_run(stack_readings=a_rising_then_easing_log)

    assert StackVoltage.find_highest_volts(run) == 12.0


def test_it_finds_the_volts_the_run_started_at(a_run, a_rising_then_easing_log):
    run = a_run(stack_readings=a_rising_then_easing_log)

    assert StackVoltage.find_starting_volts(run) == 5.0


def test_the_start_is_the_earliest_minute_not_the_order_it_arrives(a_run, a_stack_reading):
    run = a_run(stack_readings=(a_stack_reading(minute=60, supply_voltage_v=8.0),
                                a_stack_reading(minute=0, supply_voltage_v=5.0)))

    assert StackVoltage.find_starting_volts(run) == 5.0


def test_the_start_is_the_earliest_minute_that_has_a_voltage(a_run, a_stack_reading):
    """The supply was often switched on a minute or two after the log began."""
    run = a_run(stack_readings=(a_stack_reading(minute=0, supply_voltage_v=None),
                                a_stack_reading(minute=5, supply_voltage_v=6.0),
                                a_stack_reading(minute=60, supply_voltage_v=9.0)))

    assert StackVoltage.find_starting_volts(run) == 6.0


def test_the_start_is_not_the_lowest_of_the_run(a_run, a_stack_reading):
    """A run can settle below where it started, and the start is still the start."""
    run = a_run(stack_readings=(a_stack_reading(minute=0, supply_voltage_v=7.0),
                                a_stack_reading(minute=60, supply_voltage_v=4.0)))

    assert StackVoltage.find_starting_volts(run) == 7.0


def test_a_minute_without_a_voltage_is_passed_over(a_run, a_stack_reading):
    run = a_run(stack_readings=(a_stack_reading(minute=0, supply_voltage_v=5.0),
                                a_stack_reading(minute=30, supply_voltage_v=None),
                                a_stack_reading(minute=60, supply_voltage_v=8.0)))

    assert StackVoltage.find_highest_volts(run) == 8.0


def test_one_minute_of_the_log_is_both_the_highest_and_the_start(a_run, a_stack_reading):
    run = a_run(stack_readings=(a_stack_reading(minute=30, supply_voltage_v=11.0),))

    assert StackVoltage.find_highest_volts(run) == 11.0
    assert StackVoltage.find_starting_volts(run) == 11.0


def test_a_log_that_recorded_no_voltage_at_all_gives_nothing(a_run, a_stack_reading):
    run = a_run(stack_readings=(a_stack_reading(minute=0, supply_voltage_v=None),))

    assert StackVoltage.find_highest_volts(run) is None
    assert StackVoltage.find_starting_volts(run) is None


def test_a_run_with_no_power_log_at_all_is_not_an_error(a_run):
    assert StackVoltage.find_highest_volts(a_run()) is None
    assert StackVoltage.find_starting_volts(a_run()) is None


def test_it_changes_nothing(a_run, a_rising_then_easing_log):
    run = a_run(stack_readings=a_rising_then_easing_log)

    StackVoltage.find_highest_volts(run)

    assert [reading.supply_voltage_v for reading in run.stack_readings] == [5.0, 12.0, 8.0]
