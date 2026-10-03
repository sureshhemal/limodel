"""FeedRatio: the feed's lithium to magnesium ratio, from the tank and from the setup."""

import pytest

from limodel.analyzer.calculate.constants import CONCENTRATE, DILUTE
from limodel.analyzer.calculate.quantities.feed_ratio import FeedRatio


@pytest.fixture
def a_dilute_reading(a_sampled_reading):
    """1.000 L of dilute, so 69.4 mg/L of Li is 10 mmol/L and 243.05 of Mg is 10 mmol/L."""
    def build(minute=0, weight_g=1100, li_mg_l=69.4, mg_mg_l=243.05):
        return a_sampled_reading(tank=DILUTE, minute=minute, weight_g=weight_g,
                                 li_mg_l=li_mg_l, mg_mg_l=mg_mg_l)
    return build


def test_it_finds_the_measured_ratio_of_the_dilute(a_run, a_dilute_reading):
    """10 mmol/L of Li against 10 mmol/L of Mg is 1.0."""
    run = a_run(tank_readings=(a_dilute_reading(),))

    assert FeedRatio.find_li_over_mg_in_the_dilute(run) == pytest.approx(1.0)


def test_the_measured_ratio_is_read_at_the_first_sampled_minute(a_run, a_dilute_reading):
    """Minute 60 holds half the lithium; the ratio must still be the 1.0 of minute 0."""
    run = a_run(tank_readings=(a_dilute_reading(minute=60, li_mg_l=34.7),
                               a_dilute_reading(minute=0)))

    assert FeedRatio.find_li_over_mg_in_the_dilute(run) == pytest.approx(1.0)


def test_the_measured_ratio_does_not_care_how_much_liquid_is_in_the_tank(a_run,
                                                                        a_dilute_reading):
    """2.000 L of the same feed: both metals double, so the litres cancel out."""
    run = a_run(tank_readings=(a_dilute_reading(weight_g=2100),))

    assert FeedRatio.find_li_over_mg_in_the_dilute(run) == pytest.approx(1.0)


def test_a_magnesium_rich_feed_measures_below_one(a_run, a_dilute_reading):
    """10 mmol/L of Li against 20 mmol/L of Mg is 0.5."""
    run = a_run(tank_readings=(a_dilute_reading(mg_mg_l=486.10),))

    assert FeedRatio.find_li_over_mg_in_the_dilute(run) == pytest.approx(0.5)


def test_a_minute_missing_one_metal_is_passed_over(a_run, a_dilute_reading):
    """Minute 0 has no magnesium result, so minute 60 is the first minute that can answer."""
    run = a_run(tank_readings=(a_dilute_reading(minute=0, mg_mg_l=None),
                               a_dilute_reading(minute=60, mg_mg_l=486.10)))

    assert FeedRatio.find_li_over_mg_in_the_dilute(run) == pytest.approx(0.5)


def test_a_dilute_minute_without_a_weight_cannot_be_the_feed(a_run, a_dilute_reading):
    run = a_run(tank_readings=(a_dilute_reading(minute=0, weight_g=None),))

    assert FeedRatio.find_li_over_mg_in_the_dilute(run) is None


def test_the_concentrate_is_not_the_feed(a_run, a_sampled_reading):
    run = a_run(tank_readings=(a_sampled_reading(tank=CONCENTRATE, minute=0, weight_g=1100,
                                                 li_mg_l=69.4, mg_mg_l=243.05),))

    assert FeedRatio.find_li_over_mg_in_the_dilute(run) is None


def test_a_run_with_no_readings_at_all_has_no_measured_ratio(a_run):
    assert FeedRatio.find_li_over_mg_in_the_dilute(a_run()) is None


def test_a_feed_with_no_magnesium_has_no_measured_ratio(a_run, a_dilute_reading):
    """Nothing to divide by, and a ratio against nothing is not a large ratio."""
    run = a_run(tank_readings=(a_dilute_reading(mg_mg_l=0),))

    assert FeedRatio.find_li_over_mg_in_the_dilute(run) is None


def test_it_finds_the_set_up_ratio_the_other_way_up(a_run):
    """20 mmol/L of Mg against 10 mmol/L of Li is 2.0."""
    run = a_run(li_feed_mg_l=69.4, mg_feed_mg_l=486.10)

    assert FeedRatio.find_mg_over_li_from_the_setup(run) == pytest.approx(2.0)


def test_the_set_up_ratio_needs_no_readings(a_run):
    """It is written on the setup sheet, so a run with nothing measured still has one."""
    run = a_run(li_feed_mg_l=69.4, mg_feed_mg_l=243.05, tank_readings=())

    assert FeedRatio.find_mg_over_li_from_the_setup(run) == pytest.approx(1.0)


def test_a_setup_without_a_lithium_feed_has_no_ratio(a_run):
    """A run demands a number for its feed, so a blank one is cleared after the fact."""
    run = a_run().model_copy(update={"li_feed_mg_l": None})

    assert FeedRatio.find_mg_over_li_from_the_setup(run) is None


def test_a_setup_without_a_magnesium_feed_has_no_ratio(a_run):
    run = a_run().model_copy(update={"mg_feed_mg_l": None})

    assert FeedRatio.find_mg_over_li_from_the_setup(run) is None


def test_a_setup_with_no_lithium_in_the_feed_has_no_ratio(a_run):
    assert FeedRatio.find_mg_over_li_from_the_setup(a_run(li_feed_mg_l=0)) is None
