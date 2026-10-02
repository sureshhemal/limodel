"""DropRunsMissingAnEndSample: a run the lab cannot answer for has no result to give."""

import pytest

from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess.steps.drop_runs_missing_an_end_sample import DropRunsMissingAnEndSample
from limodel.models import Sample, TankReading


def sampled(tank, minute, li, mg, run_code="AA"):
    """One reading with a sample drawn from it, measured or not."""
    sample = Sample(sample_id=f"{run_code}{tank}{minute}", run_code=run_code, minute=minute,
                    tank=tank, li_mg_l=li, mg_mg_l=mg)

    return TankReading(run_code=run_code, minute=minute, tank=tank, sample=sample)


def both_ends(run_code="AA", ends=(0, 240), **missing):
    """Readings for a run the lab has answered for, with whatever a test takes away."""
    readings = []
    for tank in ("conc", "dil"):
        for minute in ends:
            li, mg = missing.get(f"{tank}{minute}", (100.0, 50.0))
            readings.append(sampled(tank, minute, li, mg, run_code))

    return readings


@pytest.fixture
def step():
    return DropRunsMissingAnEndSample()


def test_a_run_measured_at_both_ends_is_kept(step, a_run):
    runs = [a_run(tank_readings=both_ends())]

    assert step.apply(runs, Journal()) == runs


def test_a_run_the_lab_has_not_touched_is_dropped(step, a_run, readings):
    runs = [a_run(tank_readings=readings(weight_g=(2119.7, 2117.8)))]

    assert step.apply(runs, Journal()) == []


def test_a_run_missing_the_last_sample_is_dropped(step, a_run):
    """AU's shape: the start of both tanks and the end of only one."""
    runs = [a_run(tank_readings=both_ends(dil240=(None, None)))]

    assert step.apply(runs, Journal()) == []


def test_a_run_missing_the_first_sample_is_dropped(step, a_run):
    runs = [a_run(tank_readings=both_ends(conc0=(None, None)))]

    assert step.apply(runs, Journal()) == []


def test_lithium_without_magnesium_is_not_enough(step, a_run):
    """Permselectivity is a ratio of ratios, so one metal cannot answer for the other."""
    runs = [a_run(tank_readings=both_ends(conc240=(210.5, None)))]

    assert step.apply(runs, Journal()) == []


def test_a_run_sampled_once_is_dropped(step, a_run):
    """A start with no end: nothing moved between two moments that can be measured."""
    runs = [a_run(tank_readings=both_ends(ends=(0,)))]

    assert step.apply(runs, Journal()) == []


def test_the_rinse_is_not_asked_for(step, a_run):
    """It is not part of the chemistry, so a run is not dropped for lacking its samples."""
    runs = [a_run(tank_readings=both_ends())]

    assert step.apply(runs, Journal()) == runs


def test_the_samples_in_between_are_not_asked_for(step, a_run):
    """They draw the picture of a run; the model is fitted on the two ends."""
    readings = [*both_ends(), sampled("conc", 120, None, None), sampled("dil", 120, None, None)]
    runs = [a_run(tank_readings=readings)]

    assert step.apply(runs, Journal()) == runs


def test_it_keeps_the_runs_it_can_and_drops_the_rest(step, a_run):
    kept = a_run(run_code="AA", tank_readings=both_ends())
    gone = a_run(run_code="BB", tank_readings=both_ends("BB", dil240=(None, None)))

    assert step.apply([kept, gone], Journal()) == [kept]


def test_the_list_it_is_given_is_not_changed(step, a_run):
    runs = [a_run(tank_readings=both_ends(conc0=(None, None)))]
    before = list(runs)

    step.apply(runs, Journal())

    assert runs == before


def test_no_runs_at_all_is_not_an_error(step):
    assert step.apply([], Journal()) == []
