"""ChargeThatPassed: the coulombs under the supply current against time."""

import pytest

from limodel.analyzer.calculate.quantities.charge_that_passed import ChargeThatPassed


@pytest.fixture
def an_hour_at_a_tenth_of_an_amp(a_stack_reading):
    """0.1 A held from minute 0 to minute 60 is 6 amp-minutes, so 360 C."""
    return (a_stack_reading(minute=0, supply_current_a=0.1),
            a_stack_reading(minute=60, supply_current_a=0.1))


def test_it_finds_the_coulombs_of_a_steady_current(a_run, an_hour_at_a_tenth_of_an_amp):
    run = a_run(stack_readings=an_hour_at_a_tenth_of_an_amp)

    assert ChargeThatPassed.find_coulombs(run) == 360.0


def test_a_current_that_rises_is_averaged_across_the_gap(a_run, a_stack_reading):
    """0.1 A to 0.3 A over 60 minutes averages 0.2 A, so 12 amp-minutes and 720 C."""
    run = a_run(stack_readings=(a_stack_reading(minute=0, supply_current_a=0.1),
                                a_stack_reading(minute=60, supply_current_a=0.3)))

    assert ChargeThatPassed.find_coulombs(run) == 720.0


def test_every_gap_in_the_log_is_counted(a_run, a_stack_reading):
    """0.2 A over the first 30 minutes and 0.3 A over the next is 6 + 9 amp-minutes."""
    run = a_run(stack_readings=(a_stack_reading(minute=0, supply_current_a=0.1),
                                a_stack_reading(minute=30, supply_current_a=0.3),
                                a_stack_reading(minute=60, supply_current_a=0.3)))

    assert ChargeThatPassed.find_coulombs(run) == 900.0


def test_the_log_is_read_in_minute_order_not_the_order_it_arrives(a_run, a_stack_reading):
    """Taken in the order given, the last gap would be negative and cancel the first."""
    run = a_run(stack_readings=(a_stack_reading(minute=60, supply_current_a=0.3),
                                a_stack_reading(minute=0, supply_current_a=0.1),
                                a_stack_reading(minute=30, supply_current_a=0.3)))

    assert ChargeThatPassed.find_coulombs(run) == 900.0


def test_a_minute_without_a_current_is_passed_over(a_run, a_stack_reading,
                                                   an_hour_at_a_tenth_of_an_amp):
    run = a_run(stack_readings=(a_stack_reading(minute=30, supply_current_a=None),
                                *an_hour_at_a_tenth_of_an_amp))

    assert ChargeThatPassed.find_coulombs(run) == 360.0


def test_one_minute_of_the_log_cannot_say_what_charge_passed(a_run, a_stack_reading):
    """A single current says nothing about how long it was held for."""
    run = a_run(stack_readings=(a_stack_reading(minute=0, supply_current_a=0.1),))

    assert ChargeThatPassed.find_coulombs(run) is None


def test_a_run_with_no_power_log_at_all_is_not_an_error(a_run):
    assert ChargeThatPassed.find_coulombs(a_run()) is None


def test_it_reports_the_charge_over_the_area(a_run, an_hour_at_a_tenth_of_an_amp):
    """360 C is 0.1 A*h, and over 10 cm2 that is 10 mA*h/cm2."""
    run = a_run(area_cm2=10.0, stack_readings=an_hour_at_a_tenth_of_an_amp)

    assert ChargeThatPassed.find_mah_per_cm2(run) == 10.0


def test_a_smaller_area_carries_a_denser_charge(a_run, an_hour_at_a_tenth_of_an_amp):
    """The same 360 C over 5 cm2 is 20 mA*h/cm2."""
    run = a_run(area_cm2=5.0, stack_readings=an_hour_at_a_tenth_of_an_amp)

    assert ChargeThatPassed.find_mah_per_cm2(run) == 20.0


def test_no_area_cannot_be_divided_into(a_run, an_hour_at_a_tenth_of_an_amp):
    run = a_run(area_cm2=0.0, stack_readings=an_hour_at_a_tenth_of_an_amp)

    assert ChargeThatPassed.find_mah_per_cm2(run) is None


def test_no_charge_cannot_be_spread_over_the_area(a_run):
    assert ChargeThatPassed.find_mah_per_cm2(a_run()) is None


def test_it_changes_nothing(a_run, a_stack_reading):
    run = a_run(stack_readings=(a_stack_reading(minute=60, supply_current_a=0.3),
                                a_stack_reading(minute=0, supply_current_a=0.1)))

    ChargeThatPassed.find_coulombs(run)

    assert [reading.minute for reading in run.stack_readings] == [60, 0]
