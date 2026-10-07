"""BalanceGap: the percent of what the dilute lost that the readings never account for."""

import pytest

from limodel.analyzer.calculate.constants import CONCENTRATE, DILUTE, RINSE
from limodel.analyzer.calculate.metal import LITHIUM, MAGNESIUM, Metal
from limodel.analyzer.calculate.quantities.balance_gap import BalanceGap


@pytest.fixture
def every_tank_sampled_twice(a_sampled_reading):
    """Every tank is 2.000 L, so each mg/L here is two milligrams in the tank.

    Lithium: the feed loses 400 mg, the concentrate gains 300 and the rinse 20, a gap of 80.
    Magnesium: the feed loses 800 mg, the concentrate gains 600 and the rinse 80, a gap 120.
    """
    return (a_sampled_reading(tank=DILUTE, minute=0, weight_g=2100,
                              li_mg_l=500, mg_mg_l=1000),
            a_sampled_reading(tank=DILUTE, minute=60, weight_g=2100,
                              li_mg_l=300, mg_mg_l=600),
            a_sampled_reading(tank=CONCENTRATE, minute=0, weight_g=2100,
                              li_mg_l=50, mg_mg_l=100),
            a_sampled_reading(tank=CONCENTRATE, minute=60, weight_g=2100,
                              li_mg_l=200, mg_mg_l=400),
            a_sampled_reading(tank=RINSE, minute=0, weight_g=2100,
                              li_mg_l=5, mg_mg_l=10),
            a_sampled_reading(tank=RINSE, minute=60, weight_g=2100,
                              li_mg_l=15, mg_mg_l=50))


def test_it_finds_the_percent_nothing_accounts_for(a_run, every_tank_sampled_twice):
    """100 * 80 / 400 is 20 percent."""
    run = a_run(tank_readings=every_tank_sampled_twice)

    assert BalanceGap.find_percent(run, LITHIUM) == 20.0


def test_it_finds_the_gap_for_either_metal(a_run, every_tank_sampled_twice):
    """100 * 120 / 800 is 15 percent."""
    run = a_run(tank_readings=every_tank_sampled_twice)

    assert BalanceGap.find_percent(run, MAGNESIUM) == 15.0


def test_a_rinse_that_was_never_weighed_counts_as_nothing_gained(a_run,
                                                                 every_tank_sampled_twice):
    """Without the rinse's 20 mg the gap grows to 100 * 100 / 400, which is 25 percent."""
    without_the_rinse = [reading for reading in every_tank_sampled_twice
                         if reading.tank != RINSE]
    run = a_run(tank_readings=without_the_rinse)

    assert BalanceGap.find_percent(run, LITHIUM) == 25.0


def test_the_gap_is_negative_when_more_was_found_than_was_lost(a_run, a_sampled_reading):
    """A feed down 400 mg and a concentrate up 500 mg is 100 * -100 / 400, minus 25."""
    run = a_run(tank_readings=(
        a_sampled_reading(tank=DILUTE, minute=0, weight_g=2100, li_mg_l=500),
        a_sampled_reading(tank=DILUTE, minute=60, weight_g=2100, li_mg_l=300),
        a_sampled_reading(tank=CONCENTRATE, minute=0, weight_g=2100, li_mg_l=50),
        a_sampled_reading(tank=CONCENTRATE, minute=60, weight_g=2100, li_mg_l=300)))

    assert BalanceGap.find_percent(run, LITHIUM) == -25.0


def test_a_feed_that_lost_nothing_cannot_be_judged(a_run, a_sampled_reading):
    """Zero lost on the bottom of the division, so there is no share of it to report."""
    run = a_run(tank_readings=(
        a_sampled_reading(tank=DILUTE, minute=0, weight_g=2100, li_mg_l=500),
        a_sampled_reading(tank=DILUTE, minute=60, weight_g=2100, li_mg_l=500),
        a_sampled_reading(tank=CONCENTRATE, minute=0, weight_g=2100, li_mg_l=50),
        a_sampled_reading(tank=CONCENTRATE, minute=60, weight_g=2100, li_mg_l=200)))

    assert BalanceGap.find_percent(run, LITHIUM) is None


def test_a_feed_that_ended_fuller_than_it_started_cannot_be_judged(a_run, a_sampled_reading):
    """A feed up 400 mg lost nothing, so there is no loss for the gap to be a share of."""
    run = a_run(tank_readings=(
        a_sampled_reading(tank=DILUTE, minute=0, weight_g=2100, li_mg_l=300),
        a_sampled_reading(tank=DILUTE, minute=60, weight_g=2100, li_mg_l=500),
        a_sampled_reading(tank=CONCENTRATE, minute=0, weight_g=2100, li_mg_l=50),
        a_sampled_reading(tank=CONCENTRATE, minute=60, weight_g=2100, li_mg_l=200)))

    assert BalanceGap.find_percent(run, LITHIUM) is None


def test_a_run_whose_concentrate_was_never_sampled_cannot_be_judged(a_run,
                                                                    a_sampled_reading):
    """The concentrate holds most of what moved, so guessing it as nothing would mislead."""
    run = a_run(tank_readings=(
        a_sampled_reading(tank=DILUTE, minute=0, weight_g=2100, li_mg_l=500),
        a_sampled_reading(tank=DILUTE, minute=60, weight_g=2100, li_mg_l=300)))

    assert BalanceGap.find_percent(run, LITHIUM) is None


def test_a_run_whose_feed_was_never_sampled_cannot_be_judged(a_run, a_sampled_reading):
    run = a_run(tank_readings=(
        a_sampled_reading(tank=CONCENTRATE, minute=0, weight_g=2100, li_mg_l=50),
        a_sampled_reading(tank=CONCENTRATE, minute=60, weight_g=2100, li_mg_l=200)))

    assert BalanceGap.find_percent(run, LITHIUM) is None


def test_a_minute_the_lab_reported_no_metal_for_is_passed_over(a_run, a_sampled_reading,
                                                               every_tank_sampled_twice):
    run = a_run(tank_readings=(
        *every_tank_sampled_twice,
        a_sampled_reading(tank=DILUTE, minute=90, weight_g=2100, li_mg_l=None)))

    assert BalanceGap.find_percent(run, LITHIUM) == 20.0


def test_a_minute_without_a_weight_is_passed_over(a_run, a_sampled_reading,
                                                  every_tank_sampled_twice):
    """Without a weight there is no volume, so its concentration cannot become milligrams."""
    run = a_run(tank_readings=(
        *every_tank_sampled_twice,
        a_sampled_reading(tank=CONCENTRATE, minute=90, weight_g=None, li_mg_l=900)))

    assert BalanceGap.find_percent(run, LITHIUM) == 20.0


def test_a_metal_the_lab_never_reported_cannot_be_judged(a_run, every_tank_sampled_twice):
    """Lithium and magnesium sit on these samples; sodium does not."""
    run = a_run(tank_readings=every_tank_sampled_twice)
    sodium = Metal("sodium", "na_mg_l", 22.99, 1)

    assert BalanceGap.find_percent(run, sodium) is None


def test_one_sampled_minute_a_tank_cannot_be_judged(a_run, a_sampled_reading):
    """A single minute spans nothing, so neither the loss nor the gain exists."""
    run = a_run(tank_readings=(
        a_sampled_reading(tank=DILUTE, minute=0, weight_g=2100, li_mg_l=500),
        a_sampled_reading(tank=CONCENTRATE, minute=0, weight_g=2100, li_mg_l=50)))

    assert BalanceGap.find_percent(run, LITHIUM) is None


def test_a_run_with_no_readings_at_all_is_not_an_error(a_run):
    assert BalanceGap.find_percent(a_run(), LITHIUM) is None


def test_it_changes_nothing(a_run, every_tank_sampled_twice):
    run = a_run(tank_readings=every_tank_sampled_twice)

    BalanceGap.find_percent(run, LITHIUM)

    assert [reading.tank for reading in run.tank_readings] == [
        DILUTE, DILUTE, CONCENTRATE, CONCENTRATE, RINSE, RINSE]
