"""LithiumRecovery: the percent of the feed's lithium that ended up in the concentrate."""

import pytest

from limodel.analyzer.calculate.constants import CONCENTRATE, DILUTE
from limodel.analyzer.calculate.quantities.lithium_recovery import LithiumRecovery


@pytest.fixture
def a_run_that_recovered_thirty_percent(a_run, a_sampled_reading):
    """Every tank is 2.000 L: the feed starts with 1000 mg of Li, the concentrate gains 300.

    100 * 300 / 1000 is 30 percent.
    """
    return a_run(tank_readings=(
        a_sampled_reading(tank=DILUTE, minute=0, weight_g=2100, li_mg_l=500),
        a_sampled_reading(tank=DILUTE, minute=60, weight_g=2100, li_mg_l=300),
        a_sampled_reading(tank=CONCENTRATE, minute=0, weight_g=2100, li_mg_l=50),
        a_sampled_reading(tank=CONCENTRATE, minute=60, weight_g=2100, li_mg_l=200)))


def test_it_finds_the_percent_that_crossed(a_run_that_recovered_thirty_percent):
    assert LithiumRecovery.find_percent(a_run_that_recovered_thirty_percent) == 30.0


def test_it_measures_against_the_feeds_first_minute_not_its_last(
        a_run_that_recovered_thirty_percent):
    """Against the 600 mg the feed ended with, the same 300 mg would read 50 percent."""
    assert LithiumRecovery.find_percent(a_run_that_recovered_thirty_percent) == 30.0


def test_a_run_whose_concentrate_was_never_sampled_cannot_say(a_run, a_sampled_reading):
    run = a_run(tank_readings=(
        a_sampled_reading(tank=DILUTE, minute=0, weight_g=2100, li_mg_l=500),
        a_sampled_reading(tank=DILUTE, minute=60, weight_g=2100, li_mg_l=300)))

    assert LithiumRecovery.find_percent(run) is None


def test_a_run_whose_feed_was_never_sampled_cannot_say(a_run, a_sampled_reading):
    run = a_run(tank_readings=(
        a_sampled_reading(tank=CONCENTRATE, minute=0, weight_g=2100, li_mg_l=50),
        a_sampled_reading(tank=CONCENTRATE, minute=60, weight_g=2100, li_mg_l=200)))

    assert LithiumRecovery.find_percent(run) is None


def test_a_minute_the_lab_reported_no_lithium_for_is_passed_over(
        a_run, a_sampled_reading, a_run_that_recovered_thirty_percent):
    run = a_run(tank_readings=(
        *a_run_that_recovered_thirty_percent.tank_readings,
        a_sampled_reading(tank=DILUTE, minute=90, weight_g=2100, li_mg_l=None)))

    assert LithiumRecovery.find_percent(run) == 30.0


def test_a_minute_without_a_weight_is_passed_over(
        a_run, a_sampled_reading, a_run_that_recovered_thirty_percent):
    """Without a weight there is no volume, so its concentration cannot become milligrams."""
    run = a_run(tank_readings=(
        *a_run_that_recovered_thirty_percent.tank_readings,
        a_sampled_reading(tank=CONCENTRATE, minute=90, weight_g=None, li_mg_l=900)))

    assert LithiumRecovery.find_percent(run) == 30.0


def test_one_sampled_minute_a_tank_cannot_say(a_run, a_sampled_reading):
    """Nothing crossed over a single minute, so there is no span to measure."""
    run = a_run(tank_readings=(
        a_sampled_reading(tank=DILUTE, minute=0, weight_g=2100, li_mg_l=500),
        a_sampled_reading(tank=CONCENTRATE, minute=0, weight_g=2100, li_mg_l=50)))

    assert LithiumRecovery.find_percent(run) is None


def test_a_run_with_no_readings_at_all_is_not_an_error(a_run):
    assert LithiumRecovery.find_percent(a_run()) is None


def test_a_feed_that_started_with_no_lithium_cannot_be_recovered_from(
        a_run, a_sampled_reading):
    """Zero of the prize on the bottom of the division, so there is no percent to give."""
    run = a_run(tank_readings=(
        a_sampled_reading(tank=DILUTE, minute=0, weight_g=2100, li_mg_l=0),
        a_sampled_reading(tank=DILUTE, minute=60, weight_g=2100, li_mg_l=0),
        a_sampled_reading(tank=CONCENTRATE, minute=0, weight_g=2100, li_mg_l=50),
        a_sampled_reading(tank=CONCENTRATE, minute=60, weight_g=2100, li_mg_l=200)))

    assert LithiumRecovery.find_percent(run) is None


def test_a_concentrate_that_gained_nothing_is_zero_percent(a_run, a_sampled_reading):
    run = a_run(tank_readings=(
        a_sampled_reading(tank=DILUTE, minute=0, weight_g=2100, li_mg_l=500),
        a_sampled_reading(tank=DILUTE, minute=60, weight_g=2100, li_mg_l=300),
        a_sampled_reading(tank=CONCENTRATE, minute=0, weight_g=2100, li_mg_l=50),
        a_sampled_reading(tank=CONCENTRATE, minute=60, weight_g=2100, li_mg_l=50)))

    assert LithiumRecovery.find_percent(run) == 0.0


def test_it_changes_nothing(a_run_that_recovered_thirty_percent):
    LithiumRecovery.find_percent(a_run_that_recovered_thirty_percent)

    assert [reading.minute for reading
            in a_run_that_recovered_thirty_percent.tank_readings] == [0, 60, 0, 60]
