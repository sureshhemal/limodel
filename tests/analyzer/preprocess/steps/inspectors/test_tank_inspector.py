"""TankInspector: each tank is judged on its own readings, in time order."""

from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess.steps.inspectors.tank_inspector import TankInspector
from tests.analyzer.preprocess.steps.inspectors.test_inspector import RejectTheHeaviest


class ConcTank(TankInspector):
    tank = "conc"

    def _checks(self):
        return (RejectTheHeaviest(),)


def test_it_looks_only_at_its_own_tank(a_run, readings):
    mine = readings(tank="conc", weight_g=(900.0, 2000.0))
    theirs = readings(tank="dil", weight_g=(900.0, 3000.0))

    ConcTank().inspect(a_run(tank_readings=mine + theirs), Journal())

    assert [reading.weight_g for reading in theirs] == [900.0, 3000.0]
    assert [reading.weight_g for reading in mine] == [900.0, None]


def test_it_puts_the_readings_in_time_order(a_run, readings):
    """The file may hold them in any order; a rate or a jump needs them in the right one."""
    given = readings(weight_g=(900.0, 800.0, 700.0), minutes=(30, 0, 15))

    looked_at = ConcTank().inspect(a_run(tank_readings=given), Journal())

    assert [reading.minute for reading in looked_at] == [0, 15, 30]


def test_a_tank_with_no_readings_is_not_an_error(a_run, readings):
    theirs = readings(tank="rinse", weight_g=(900.0, 3000.0))

    assert ConcTank().inspect(a_run(tank_readings=theirs), Journal()) == []
