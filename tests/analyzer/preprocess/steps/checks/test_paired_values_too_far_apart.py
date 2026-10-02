"""PairedValuesTooFarApart: two voltage readings too far apart, and which one lied."""

import pytest

from limodel.analyzer.preprocess.steps.checks.instrument import Instrument
from limodel.analyzer.preprocess.steps.checks.paired_values_too_far_apart import PairedValuesTooFarApart


@pytest.fixture
def check():
    """The two voltages, as the power log inspector sets them up."""
    return PairedValuesTooFarApart(Instrument("supply_voltage_v", "the supply", "V"),
                                   Instrument("meter_voltage_v", "the multimeter", "V"),
                                   "voltage", largest_gap=1.0)


def test_instruments_that_agree_are_accepted(check, power_readings):
    given = power_readings(supply_voltage_v=(11.47, 11.38, 11.33),
                           meter_voltage_v=(11.45, 11.34, 11.28))

    assert check.find_worst_offender(given) is None


def test_the_meter_is_blamed_when_it_loses_a_digit(check, power_readings):
    given = power_readings(supply_voltage_v=(11.23, 11.2, 11.15),
                           meter_voltage_v=(11.18, 1.16, 11.09))

    reading, field_name, reason = check.find_worst_offender(given)

    assert reading is given[1]
    assert field_name == "meter_voltage_v"
    assert reason == ("the two voltage readings differ by 10.04 V, and the multimeter's "
                      "1.16 V is unlike its own column")


def test_the_supply_is_blamed_when_it_gains_a_digit(check, power_readings):
    """The meter is the honest one here, so the supply is the value cleared."""
    given = power_readings(supply_voltage_v=(10.15, 100.06, 9.98),
                           meter_voltage_v=(10.08, 10.0, 9.93))

    reading, field_name, _ = check.find_worst_offender(given)

    assert reading is given[1]
    assert field_name == "supply_voltage_v"


def test_it_takes_the_widest_disagreement_first(check, power_readings):
    given = power_readings(supply_voltage_v=(11.2, 11.15, 11.1),
                           meter_voltage_v=(1.12, 11.09, 9.9))

    reading, _, _ = check.find_worst_offender(given)

    assert reading is given[0]


def test_a_gap_at_the_limit_is_allowed(check, power_readings):
    given = power_readings(supply_voltage_v=(11.2, 11.2), meter_voltage_v=(11.2, 10.2))

    assert check.find_worst_offender(given) is None


def test_a_reading_with_only_one_instrument_is_passed_over(check, power_readings):
    given = power_readings(supply_voltage_v=(11.2, 11.15), meter_voltage_v=(None, 11.09))

    assert check.find_worst_offender(given) is None


def test_no_readings_at_all_is_not_an_error(check):
    assert check.find_worst_offender([]) is None


def test_it_changes_nothing(check, power_readings):
    given = power_readings(supply_voltage_v=(11.23, 11.2), meter_voltage_v=(11.18, 1.16))

    check.find_worst_offender(given)

    assert [reading.meter_voltage_v for reading in given] == [11.18, 1.16]
