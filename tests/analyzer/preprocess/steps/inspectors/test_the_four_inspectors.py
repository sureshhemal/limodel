"""The four inspectors: which readings each one looks at, and what it holds them to."""

import pytest

from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess.steps.checks.paired_values_out_of_proportion import PairedValuesOutOfProportion
from limodel.analyzer.preprocess.steps.checks.paired_values_too_far_apart import PairedValuesTooFarApart
from limodel.analyzer.preprocess.steps.checks.jump_that_comes_back import JumpThatComesBack
from limodel.analyzer.preprocess.steps.checks.value_far_from_the_median import ValueFarFromTheMedian
from limodel.analyzer.preprocess.steps.checks.value_moving_too_fast import ValueMovingTooFast
from limodel.analyzer.preprocess.steps.checks.value_outside_the_range import ValueOutsideTheRange
from limodel.analyzer.preprocess.steps.inspectors.conc_tank_inspector import ConcTankInspector
from limodel.analyzer.preprocess.steps.inspectors.diluate_tank_inspector import DiluateTankInspector
from limodel.analyzer.preprocess.steps.inspectors.power_log_inspector import PowerLogInspector
from limodel.analyzer.preprocess.steps.inspectors.rinse_tank_inspector import RinseTankInspector
from limodel.analyzer.thresholds import Thresholds

TANKS = [ConcTankInspector, DiluateTankInspector, RinseTankInspector]
EVERY_INSPECTOR = [*TANKS, PowerLogInspector]

WHAT_A_TANK_IS_HELD_TO = [
    (ValueFarFromTheMedian, "weight_g"),
    (ValueOutsideTheRange, "ph"),
    (ValueMovingTooFast, "ph"),
    (ValueOutsideTheRange, "temp_c"),
    (ValueMovingTooFast, "temp_c"),
    (JumpThatComesBack, "conductivity_us_cm"),
]

WHAT_THE_POWER_LOG_IS_HELD_TO = [
    (ValueFarFromTheMedian, "supply_current_a"),
    (PairedValuesTooFarApart, "supply_voltage_v"),
    (PairedValuesOutOfProportion, "supply_current_a"),
]


@pytest.mark.parametrize("inspector, tank", list(zip(TANKS, ["conc", "dil", "rinse"])))
def test_each_tank_inspector_names_its_own_tank(inspector, tank):
    assert inspector.tank == tank


@pytest.mark.parametrize("inspector", TANKS)
def test_what_each_tank_is_held_to(inspector):
    assert [(type(check), check.field_name) for check in inspector().checks] == WHAT_A_TANK_IS_HELD_TO


def test_what_the_power_log_is_held_to():
    assert [(type(check), check.field_name) for check in PowerLogInspector().checks] == (
        WHAT_THE_POWER_LOG_IS_HELD_TO)


@pytest.mark.parametrize("inspector", EVERY_INSPECTOR)
def test_the_thresholds_reach_every_check(inspector):
    """A check holding its own numbers could not be tried against different ones."""
    numbers = Thresholds(impossible_weight_share=0.5)

    assert inspector(numbers).thresholds is numbers


def test_a_tank_inspector_reads_the_tank_log(a_run, readings, power_readings):
    tank_log = readings(weight_g=(2119.7, 2117.8, 1800.0))
    power_log = power_readings(supply_current_a=(0.045, 0.045, 0.46))

    ConcTankInspector().inspect(a_run(tank_readings=tank_log, stack_readings=power_log),
                                journal := Journal())

    assert [entry.id for entry in journal.entries] == ["AA:conc:30"]


def test_the_power_log_inspector_reads_the_power_log(a_run, readings, power_readings):
    tank_log = readings(weight_g=(2119.7, 2117.8, 1800.0))
    power_log = power_readings(supply_current_a=(0.045, 0.045, 0.46))

    PowerLogInspector().inspect(a_run(tank_readings=tank_log, stack_readings=power_log),
                                journal := Journal())

    assert [entry.id for entry in journal.entries] == ["AA:30"]
