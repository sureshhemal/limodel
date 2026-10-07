"""EnergyPerMoleOfLithium: the watt-hours the run spent per mole of lithium it moved."""

import pytest

from limodel.analyzer.calculate.constants import DILUTE
from limodel.analyzer.calculate.quantities.energy_per_mole_of_lithium import EnergyPerMoleOfLithium


@pytest.fixture
def an_hour_at_one_watt(a_stack_reading):
    """10 V at 0.1 A is 1 W, held from minute 0 to minute 60: 3600 J, so 1 W*h."""
    return (a_stack_reading(minute=0, supply_voltage_v=10.0, supply_current_a=0.1),
            a_stack_reading(minute=60, supply_voltage_v=10.0, supply_current_a=0.1))


@pytest.fixture
def a_tenth_of_a_mole_into_the_concentrate(a_sampled_reading):
    """2.000 L rising from 50 to 397 mg/L is 694 mg of Li, which is exactly 0.1 mol."""
    return (a_sampled_reading(minute=0, weight_g=2100, li_mg_l=50),
            a_sampled_reading(minute=60, weight_g=2100, li_mg_l=397))


def test_it_finds_the_watt_hours_per_mole(a_run, an_hour_at_one_watt,
                                          a_tenth_of_a_mole_into_the_concentrate):
    """1 W*h over 0.1 mol is 10 W*h per mole."""
    run = a_run(stack_readings=an_hour_at_one_watt,
                tank_readings=a_tenth_of_a_mole_into_the_concentrate)

    assert EnergyPerMoleOfLithium.find_watt_hours(run) == 10.0


def test_moving_twice_the_lithium_for_the_same_power_costs_half(
        a_run, an_hour_at_one_watt, a_sampled_reading):
    """2.000 L rising from 50 to 744 mg/L is 1388 mg, which is 0.2 mol, so 5 W*h per mole."""
    run = a_run(stack_readings=an_hour_at_one_watt,
                tank_readings=(a_sampled_reading(minute=0, weight_g=2100, li_mg_l=50),
                               a_sampled_reading(minute=60, weight_g=2100, li_mg_l=744)))

    assert EnergyPerMoleOfLithium.find_watt_hours(run) == 5.0


def test_it_finds_the_joules_under_the_power_curve(a_run, an_hour_at_one_watt):
    run = a_run(stack_readings=an_hour_at_one_watt)

    assert EnergyPerMoleOfLithium.find_joules(run) == 3600.0


def test_a_power_that_rises_is_averaged_across_the_gap(a_run, a_stack_reading):
    """1 W to 3 W over 60 minutes averages 2 W, so 120 watt-minutes and 7200 J."""
    run = a_run(stack_readings=(a_stack_reading(minute=0, supply_voltage_v=10.0,
                                                supply_current_a=0.1),
                                a_stack_reading(minute=60, supply_voltage_v=10.0,
                                                supply_current_a=0.3)))

    assert EnergyPerMoleOfLithium.find_joules(run) == 7200.0


def test_the_log_is_read_in_minute_order_not_the_order_it_arrives(a_run, a_stack_reading):
    run = a_run(stack_readings=(a_stack_reading(minute=60, supply_voltage_v=10.0,
                                                supply_current_a=0.1),
                                a_stack_reading(minute=0, supply_voltage_v=10.0,
                                                supply_current_a=0.1)))

    assert EnergyPerMoleOfLithium.find_joules(run) == 3600.0


def test_a_minute_missing_either_half_of_the_power_is_passed_over(a_run, a_stack_reading,
                                                                  an_hour_at_one_watt):
    """Volts alone say nothing about watts, so the minute cannot join the curve."""
    run = a_run(stack_readings=(a_stack_reading(minute=30, supply_voltage_v=10.0,
                                                supply_current_a=None),
                                *an_hour_at_one_watt))

    assert EnergyPerMoleOfLithium.find_joules(run) == 3600.0


def test_one_minute_of_the_log_cannot_say_what_energy_went_in(
        a_run, a_stack_reading, a_tenth_of_a_mole_into_the_concentrate):
    run = a_run(stack_readings=(a_stack_reading(minute=0, supply_voltage_v=10.0,
                                                supply_current_a=0.1),),
                tank_readings=a_tenth_of_a_mole_into_the_concentrate)

    assert EnergyPerMoleOfLithium.find_joules(run) is None
    assert EnergyPerMoleOfLithium.find_watt_hours(run) is None


def test_a_run_with_no_power_log_at_all_is_not_an_error(
        a_run, a_tenth_of_a_mole_into_the_concentrate):
    run = a_run(tank_readings=a_tenth_of_a_mole_into_the_concentrate)

    assert EnergyPerMoleOfLithium.find_watt_hours(run) is None


def test_lithium_that_never_crossed_cannot_be_divided_into(a_run, an_hour_at_one_watt,
                                                           a_sampled_reading):
    """The concentrate ended where it started, so there is no per-mole cost to report."""
    run = a_run(stack_readings=an_hour_at_one_watt,
                tank_readings=(a_sampled_reading(minute=0, weight_g=2100, li_mg_l=50),
                               a_sampled_reading(minute=60, weight_g=2100, li_mg_l=50)))

    assert EnergyPerMoleOfLithium.find_watt_hours(run) is None


def test_a_concentrate_that_lost_lithium_has_no_cost_per_mole(a_run, an_hour_at_one_watt,
                                                              a_sampled_reading):
    run = a_run(stack_readings=an_hour_at_one_watt,
                tank_readings=(a_sampled_reading(minute=0, weight_g=2100, li_mg_l=397),
                               a_sampled_reading(minute=60, weight_g=2100, li_mg_l=50)))

    assert EnergyPerMoleOfLithium.find_watt_hours(run) is None


def test_lithium_the_lab_never_reported_cannot_be_divided_into(a_run, an_hour_at_one_watt,
                                                               a_sampled_reading):
    run = a_run(stack_readings=an_hour_at_one_watt,
                tank_readings=(a_sampled_reading(minute=0, weight_g=2100, mg_mg_l=100),
                               a_sampled_reading(minute=60, weight_g=2100, mg_mg_l=400)))

    assert EnergyPerMoleOfLithium.find_watt_hours(run) is None


def test_a_run_with_no_tank_readings_at_all_is_not_an_error(a_run, an_hour_at_one_watt):
    run = a_run(stack_readings=an_hour_at_one_watt)

    assert EnergyPerMoleOfLithium.find_watt_hours(run) is None


def test_only_the_concentrate_counts(a_run, an_hour_at_one_watt, a_sampled_reading):
    """The dilute falls while the concentrate rises, so counting it would cancel the gain."""
    run = a_run(stack_readings=an_hour_at_one_watt,
                tank_readings=(a_sampled_reading(tank=DILUTE, minute=0, weight_g=2100,
                                                 li_mg_l=397),
                               a_sampled_reading(tank=DILUTE, minute=60, weight_g=2100,
                                                 li_mg_l=50)))

    assert EnergyPerMoleOfLithium.find_watt_hours(run) is None


def test_it_changes_nothing(a_run, an_hour_at_one_watt,
                            a_tenth_of_a_mole_into_the_concentrate):
    run = a_run(stack_readings=an_hour_at_one_watt,
                tank_readings=a_tenth_of_a_mole_into_the_concentrate)

    EnergyPerMoleOfLithium.find_watt_hours(run)

    assert [reading.sample.li_mg_l for reading in run.tank_readings] == [50, 397]
