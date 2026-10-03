"""SkipSuspectReadings: every run past every inspector."""

from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess.steps.inspectors.conc_tank_inspector import ConcTankInspector
from limodel.analyzer.preprocess.steps.inspectors.dilute_tank_inspector import DiluteTankInspector
from limodel.analyzer.preprocess.steps.inspectors.power_log_inspector import PowerLogInspector
from limodel.analyzer.preprocess.steps.inspectors.rinse_tank_inspector import RinseTankInspector
from limodel.analyzer.preprocess.steps.skip_suspect_readings import SkipSuspectReadings
from limodel.analyzer.thresholds import Thresholds


def test_it_has_an_inspector_for_every_tank_and_one_for_the_power_log():
    assert [type(inspector) for inspector in SkipSuspectReadings().inspectors] == [
        ConcTankInspector, DiluteTankInspector, RinseTankInspector, PowerLogInspector]


def test_the_thresholds_reach_the_inspectors():
    numbers = Thresholds(impossible_weight_share=0.5)

    assert all(inspector.thresholds is numbers
               for inspector in SkipSuspectReadings(numbers).inspectors)


def test_every_tank_and_the_power_log_of_every_run_is_looked_at(a_run, readings, power_readings):
    runs = [a_run(tank_readings=readings(tank="conc", weight_g=(2119.7, 2117.8, 1800.0))),
            a_run(run_code="BB",
                  tank_readings=readings(tank="rinse", run_code="BB",
                                         weight_g=(4074.8, 4070.0, 3000.0)),
                  stack_readings=power_readings(run_code="BB",
                                                supply_current_a=(0.045, 0.045, 0.46)))]

    SkipSuspectReadings().apply(runs, journal := Journal())

    assert [entry.id for entry in journal.entries] == ["AA:conc:30", "BB:rinse:30", "BB:30"]


def test_every_run_is_given_back(a_run, readings):
    runs = [a_run(tank_readings=readings(weight_g=(2119.7, 2117.8, 1800.0)))]

    assert SkipSuspectReadings().apply(runs, Journal()) is runs


def test_no_run_is_dropped_however_much_is_cleared(a_run, readings):
    runs = [a_run(tank_readings=readings(weight_g=(2119.7, 2117.8, 1800.0), ph=(0.1, 0.2, 0.3)))]

    assert len(SkipSuspectReadings().apply(runs, Journal())) == 1


def blank_values(runs):
    """How many readings are missing a value, across every value a check can clear."""
    tank = ("conductivity_us_cm", "ph", "temp_c", "weight_g")
    power = ("supply_voltage_v", "supply_current_a", "meter_voltage_v", "meter_current_ma")

    return (sum(getattr(reading, field) is None
                for run in runs for reading in run.tank_readings for field in tank)
            + sum(getattr(reading, field) is None
                  for run in runs for reading in run.stack_readings for field in power))


def test_every_value_it_clears_is_written_down(a_run, readings, power_readings):
    """Nothing may vanish quietly. One method clears a value and it writes to the journal
    first, so the count of values that went must equal the count of entries."""
    runs = [a_run(
        tank_readings=readings(weight_g=(2119.7, 2117.8, 1800.0, 2110.0),
                               ph=(5.9, 0.072, 4.5, 4.6),
                               conductivity_us_cm=(17720.9, 7610.0, 17495.0, 17500.0)),
        stack_readings=power_readings(supply_voltage_v=(11.23, 11.2, 11.15),
                                      meter_voltage_v=(11.18, 1.16, 11.09)))]
    before = blank_values(runs)

    SkipSuspectReadings().apply(runs, journal := Journal())

    cleared = blank_values(runs) - before
    assert cleared > 1
    assert cleared == len(journal.entries)
