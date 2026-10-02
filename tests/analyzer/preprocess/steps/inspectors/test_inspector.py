"""Inspector: the loop that asks a check again after each value it rejects."""

import pytest

from limodel.analyzer.journal import Action, Journal
from limodel.analyzer.preprocess.steps.checks.check import Check
from limodel.analyzer.preprocess.steps.inspectors.tank_inspector import TankInspector
from limodel.analyzer.thresholds import Thresholds


class RejectTheHeaviest(Check):
    """A stand-in check: rejects the heaviest weight while any is over a kilogramme."""

    field_name = "weight_g"
    label = "weight"

    def find_worst_offender(self, readings):
        judgeable = self.find_judgeable_readings(readings)
        if not judgeable:
            return None

        heaviest = max(judgeable, key=lambda reading: reading.weight_g)

        return (heaviest, "weight_g", "over a kilogramme") if heaviest.weight_g > 1000 else None


class RejectEveryPh(Check):
    """A stand-in check on a different value, to watch two checks run in order."""

    field_name = "ph"
    label = "pH"

    def find_worst_offender(self, readings):
        judgeable = self.find_judgeable_readings(readings)

        return (judgeable[0], "ph", "no pH wanted") if judgeable else None


class ConcTank(TankInspector):
    """An inspector of the concentrate with one stand-in check."""

    tank = "conc"

    def _find_checks(self):
        return (RejectTheHeaviest(),)


class ConcTankWithTwoChecks(ConcTank):
    def _find_checks(self):
        return (RejectTheHeaviest(), RejectEveryPh())


@pytest.fixture
def inspector():
    return ConcTank()


def test_it_builds_its_checks_when_it_is_made(inspector):
    assert [type(check) for check in inspector.checks] == [RejectTheHeaviest]


def test_it_clears_nothing_a_check_accepts(inspector, a_run, readings):
    given = readings(weight_g=(900.0, 800.0, 700.0))
    journal = Journal()

    inspector.inspect(a_run(tank_readings=given), journal)

    assert [reading.weight_g for reading in given] == [900.0, 800.0, 700.0]
    assert journal.entries == ()


def test_it_clears_what_a_check_rejects(inspector, a_run, readings):
    given = readings(weight_g=(900.0, 2000.0, 700.0))

    inspector.inspect(a_run(tank_readings=given), journal := Journal())

    assert [reading.weight_g for reading in given] == [900.0, None, 700.0]
    assert [(entry.action, entry.id, entry.model, entry.field_name, entry.reason)
            for entry in journal.entries] == [
        (Action.SKIP, "AA:conc:15", "TankReading", "weight_g", "over a kilogramme")]


def test_it_keeps_going_until_the_check_finds_nothing(inspector, a_run, readings):
    """Three over the kilogramme, and a third of nine readings is three."""
    given = readings(weight_g=(900.0, 2000.0, 700.0, 1500.0, 800.0, 1200.0, 600.0, 500.0, 400.0))

    inspector.inspect(a_run(tank_readings=given), journal := Journal())

    assert [reading.weight_g for reading in given] == [
        900.0, None, 700.0, None, 800.0, None, 600.0, 500.0, 400.0]
    assert len(journal.entries) == 3


def test_it_takes_the_worst_first(inspector, a_run, readings):
    """The 5,000 goes before the 2,000, wherever they sit."""
    given = readings(weight_g=(1200.0, 5000.0, 900.0, 2000.0, 800.0, 700.0))

    inspector.inspect(a_run(tank_readings=given), journal := Journal())

    assert [entry.id for entry in journal.entries] == ["AA:conc:15", "AA:conc:45"]


def test_it_stops_at_the_cap_rather_than_emptying_a_series(inspector, a_run, readings):
    """Every reading is over the kilogramme, and a third of six is two."""
    given = readings(weight_g=(2000.0, 2100.0, 2200.0, 2300.0, 2400.0, 2500.0))

    inspector.inspect(a_run(tank_readings=given), journal := Journal())

    assert len(journal.entries) == 2
    assert [reading.weight_g for reading in given].count(None) == 2


def test_the_cap_always_allows_one(inspector, a_run, readings):
    """A third of three is one, so even a short series can lose its worst reading."""
    given = readings(weight_g=(900.0, 2000.0, 700.0))

    inspector.inspect(a_run(tank_readings=given), Journal())

    assert [reading.weight_g for reading in given].count(None) == 1


def test_the_cap_counts_only_the_readings_a_check_can_judge(inspector, a_run, readings):
    """Six readings, two of them weighed, so the cap is one and not two."""
    given = readings(weight_g=(2000.0, None, 2100.0, None, None, None))

    inspector.inspect(a_run(tank_readings=given), journal := Journal())

    assert len(journal.entries) == 1


def test_every_check_gets_its_turn(a_run, readings):
    given = readings(weight_g=(900.0, 2000.0, 700.0), ph=(5.9, 5.8, 5.7))

    ConcTankWithTwoChecks().inspect(a_run(tank_readings=given), journal := Journal())

    assert [entry.field_name for entry in journal.entries] == ["weight_g", "ph"]


def test_it_answers_with_the_readings_it_looked_at(inspector, a_run, readings):
    given = readings(weight_g=(900.0, 2000.0, 700.0))

    looked_at = inspector.inspect(a_run(tank_readings=given), Journal())

    assert [reading.minute for reading in looked_at] == [0, 15, 30]


def test_the_thresholds_it_is_given_reach_the_cap(a_run, readings):
    given = readings(weight_g=(2000.0, 2100.0, 2200.0, 2300.0, 2400.0, 2500.0))

    ConcTank(Thresholds(most_of_a_series_removable=0.9)).inspect(
        a_run(tank_readings=given), journal := Journal())

    assert len(journal.entries) == 5
