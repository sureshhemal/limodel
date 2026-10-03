"""Permselectivity: the transport ratio held against the ratio the feed offered."""

import pytest

from limodel.analyzer.calculate.constants import DILUTE
from limodel.analyzer.calculate.quantities.permselectivity import Permselectivity


@pytest.fixture
def crossing_that_mirrors_the_feed(a_sampled_reading):
    """10 mmol of each crossed into the concentrate, so t_li/t_mg is 10/20.

    Every tank here is 1.000 L, so the mg/L figures read straight as milligrams.
    """
    return (a_sampled_reading(minute=0, weight_g=1100, li_mg_l=0, mg_mg_l=0),
            a_sampled_reading(minute=60, weight_g=1100, li_mg_l=69.4, mg_mg_l=243.05))


@pytest.fixture
def a_dilute_reading(a_sampled_reading):
    """1.000 L of feed at 10 mmol/L of Li and 10 mmol/L of Mg unless a test says otherwise."""
    def build(li_mg_l=69.4, mg_mg_l=243.05):
        return a_sampled_reading(tank=DILUTE, minute=0, weight_g=1100, li_mg_l=li_mg_l,
                                 mg_mg_l=mg_mg_l)
    return build


def test_a_crossing_that_mirrors_its_feed_shows_no_preference(
        a_run, crossing_that_mirrors_the_feed, a_dilute_reading):
    """t_li/t_mg of 0.5 over a feed ratio of 1.0 is the 0.5 that means no preference."""
    run = a_run(tank_readings=(*crossing_that_mirrors_the_feed, a_dilute_reading()))

    assert Permselectivity.find_value(run) == pytest.approx(0.5)


def test_the_same_crossing_from_a_magnesium_rich_feed_shows_preference(
        a_run, crossing_that_mirrors_the_feed, a_dilute_reading):
    """The feed offered 10 mmol/L of Li to 20 of Mg, so 0.5 over 0.5 is 1.0."""
    run = a_run(tank_readings=(*crossing_that_mirrors_the_feed,
                               a_dilute_reading(mg_mg_l=486.10)))

    assert Permselectivity.find_value(run) == pytest.approx(1.0)


def test_a_stack_that_held_magnesium_back_reads_high(a_run, a_sampled_reading,
                                                     a_dilute_reading):
    """10 mmol of Li against 1 mmol of Mg is t_li/t_mg of 5, over a feed ratio of 1.0."""
    run = a_run(tank_readings=(a_sampled_reading(minute=0, weight_g=1100, li_mg_l=0,
                                                 mg_mg_l=0),
                               a_sampled_reading(minute=60, weight_g=1100, li_mg_l=69.4,
                                                 mg_mg_l=24.305),
                               a_dilute_reading()))

    assert Permselectivity.find_value(run) == pytest.approx(5.0)


def test_a_run_whose_feed_was_never_sampled_has_no_value(a_run,
                                                         crossing_that_mirrors_the_feed):
    """There is nothing to compare the crossing against."""
    run = a_run(tank_readings=crossing_that_mirrors_the_feed)

    assert Permselectivity.find_value(run) is None


def test_a_run_missing_a_metal_in_the_concentrate_has_no_value(a_run, a_sampled_reading,
                                                               a_dilute_reading):
    run = a_run(tank_readings=(a_sampled_reading(minute=0, weight_g=1100, li_mg_l=0,
                                                 mg_mg_l=None),
                               a_sampled_reading(minute=60, weight_g=1100, li_mg_l=69.4,
                                                 mg_mg_l=None),
                               a_dilute_reading()))

    assert Permselectivity.find_value(run) is None


def test_one_sampled_minute_in_the_concentrate_has_no_value(a_run, a_sampled_reading,
                                                            a_dilute_reading):
    run = a_run(tank_readings=(a_sampled_reading(minute=60, weight_g=1100, li_mg_l=69.4,
                                                 mg_mg_l=243.05),
                               a_dilute_reading()))

    assert Permselectivity.find_value(run) is None


def test_a_run_with_no_readings_at_all_is_not_an_error(a_run):
    assert Permselectivity.find_value(a_run()) is None


def test_a_feed_with_no_lithium_has_no_value(a_run, crossing_that_mirrors_the_feed,
                                             a_dilute_reading):
    """A feed ratio of zero cannot be divided by."""
    run = a_run(tank_readings=(*crossing_that_mirrors_the_feed,
                               a_dilute_reading(li_mg_l=0)))

    assert Permselectivity.find_value(run) is None


def test_a_crossing_with_no_magnesium_has_no_value(a_run, a_sampled_reading,
                                                   a_dilute_reading):
    """t_mg of zero cannot be divided by, however much lithium crossed."""
    run = a_run(tank_readings=(a_sampled_reading(minute=0, weight_g=1100, li_mg_l=0,
                                                 mg_mg_l=0),
                               a_sampled_reading(minute=60, weight_g=1100, li_mg_l=69.4,
                                                 mg_mg_l=0),
                               a_dilute_reading()))

    assert Permselectivity.find_value(run) is None
