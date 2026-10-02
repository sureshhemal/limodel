"""PairedValuesOutOfProportion: two current readings whose ratio is wrong."""

import pytest

from limodel.analyzer.preprocess.steps.checks.instrument import Instrument
from limodel.analyzer.preprocess.steps.checks.paired_values_out_of_proportion import PairedValuesOutOfProportion


@pytest.fixture
def check():
    """The two currents, as the power log inspector sets them up: amps against milliamps."""
    return PairedValuesOutOfProportion(Instrument("supply_current_a", "the supply", "A"),
                                       Instrument("meter_current_ma", "the multimeter", "mA"),
                                       "current", band=(0.62, 1.6), scale=1000)


def test_currents_in_proportion_are_accepted(check, power_readings):
    """The supply reads about a seventh higher, which is the usual state of affairs."""
    given = power_readings(supply_current_a=(0.045, 0.045), meter_current_ma=(39.5, 39.4))

    assert check.find_worst_offender(given) is None


def test_a_ratio_outside_the_band_is_rejected(check, power_readings):
    given = power_readings(supply_current_a=(0.045, 0.045, 0.045),
                           meter_current_ma=(39.5, 8.53, 39.4))

    reading, field_name, reason = check.find_worst_offender(given)

    assert reading is given[1]
    assert field_name == "meter_current_ma"
    assert reason == ("the two current readings are 5.28 times apart, outside 0.62 to 1.6, "
                      "and the multimeter's 8.53 mA is the odd one")


def test_the_supply_is_blamed_when_it_is_find_odd_one(check, power_readings):
    given = power_readings(supply_current_a=(0.045, 0.46, 0.045),
                           meter_current_ma=(39.5, 36.83, 39.4))

    reading, field_name, _ = check.find_worst_offender(given)

    assert reading is given[1]
    assert field_name == "supply_current_a"


def test_it_takes_the_worst_ratio_first(check, power_readings):
    given = power_readings(supply_current_a=(0.045, 0.045, 0.045),
                           meter_current_ma=(20.0, 8.53, 39.4))

    reading, _, _ = check.find_worst_offender(given)

    assert reading is given[1]


def test_a_reading_with_only_one_instrument_is_passed_over(check, power_readings):
    given = power_readings(supply_current_a=(0.045, 0.045), meter_current_ma=(39.5, None))

    assert check.find_worst_offender(given) is None


def test_a_meter_reading_of_zero_is_passed_over(check, power_readings):
    """Nothing can be divided by it, and the level check is what catches a dead meter."""
    given = power_readings(supply_current_a=(0.045, 0.045), meter_current_ma=(39.5, 0.0))

    assert check.find_worst_offender(given) is None


def test_it_changes_nothing(check, power_readings):
    given = power_readings(supply_current_a=(0.045, 0.045, 0.045),
                           meter_current_ma=(39.5, 8.53, 39.4))

    check.find_worst_offender(given)

    assert [reading.meter_current_ma for reading in given] == [39.5, 8.53, 39.4]
