"""AmountThatCrossed: the milligrams of a metal a tank gained between its sampled ends."""

import pytest

from limodel.analyzer.calculate.constants import CONCENTRATE, DILUTE
from limodel.analyzer.calculate.metal import LITHIUM, MAGNESIUM, Metal
from limodel.analyzer.calculate.quantities.amount_that_crossed import AmountThatCrossed


@pytest.fixture
def two_sampled_minutes(a_sampled_reading):
    """2.000 L at 50 mg/L of Li is 100 mg; 2.500 L at 200 mg/L is 500 mg."""
    return (a_sampled_reading(minute=0, weight_g=2100, li_mg_l=50, mg_mg_l=100),
            a_sampled_reading(minute=60, weight_g=2600, li_mg_l=200, mg_mg_l=400))


def test_it_finds_what_crossed_between_the_two_ends(a_run, two_sampled_minutes):
    """500 mg at the end less 100 mg at the start is 400 mg of Li."""
    run = a_run(tank_readings=two_sampled_minutes)

    assert AmountThatCrossed.find_milligrams(run, CONCENTRATE, LITHIUM) == 400.0


def test_it_finds_what_crossed_for_either_metal(a_run, two_sampled_minutes):
    """1000 mg of Mg at the end less 200 mg at the start is 800 mg."""
    run = a_run(tank_readings=two_sampled_minutes)

    assert AmountThatCrossed.find_milligrams(run, CONCENTRATE, MAGNESIUM) == 800.0


def test_it_reports_both_ends_apart(a_run, two_sampled_minutes):
    run = a_run(tank_readings=two_sampled_minutes)

    assert AmountThatCrossed.find_ends(run, CONCENTRATE, LITHIUM) == (100.0, 500.0)


def test_the_ends_are_the_earliest_and_latest_minutes_not_the_order_they_arrive(
        a_run, a_sampled_reading):
    """The loader does not promise sorted readings, so the ends are found by minute."""
    run = a_run(tank_readings=(a_sampled_reading(minute=60, weight_g=2600, li_mg_l=200),
                               a_sampled_reading(minute=0, weight_g=2100, li_mg_l=50),
                               a_sampled_reading(minute=30, weight_g=2100, li_mg_l=100)))

    assert AmountThatCrossed.find_ends(run, CONCENTRATE, LITHIUM) == (100.0, 500.0)


def test_each_tank_is_weighed_against_its_own_tare(a_run, a_sampled_reading):
    """With a 200 g tare the same weights are 2.000 L and 2.500 L again."""
    run = a_run(tare_dil_g=200.0,
                tank_readings=(a_sampled_reading(tank=DILUTE, minute=0, weight_g=2200,
                                                 li_mg_l=200),
                               a_sampled_reading(tank=DILUTE, minute=60, weight_g=2700,
                                                 li_mg_l=40)))

    assert AmountThatCrossed.find_milligrams(run, DILUTE, LITHIUM) == -300.0


def test_another_tanks_readings_are_left_out(a_run, a_sampled_reading, two_sampled_minutes):
    """The dilute falls as the concentrate rises, so mixing the tanks would cancel them."""
    run = a_run(tank_readings=(*two_sampled_minutes,
                               a_sampled_reading(tank=DILUTE, minute=0, weight_g=2100,
                                                 li_mg_l=5000)))

    assert AmountThatCrossed.find_milligrams(run, CONCENTRATE, LITHIUM) == 400.0


def test_minutes_that_were_never_sampled_are_passed_over(a_run, a_reading,
                                                         two_sampled_minutes):
    run = a_run(tank_readings=(a_reading(minute=15, weight_g=9999), *two_sampled_minutes))

    assert AmountThatCrossed.find_ends(run, CONCENTRATE, LITHIUM) == (100.0, 500.0)


def test_a_sampled_minute_without_a_weight_is_passed_over(a_run, a_sampled_reading,
                                                          two_sampled_minutes):
    """Its concentration cannot be turned into milligrams, so it cannot be an end."""
    run = a_run(tank_readings=(a_sampled_reading(minute=90, weight_g=None, li_mg_l=900),
                               *two_sampled_minutes))

    assert AmountThatCrossed.find_ends(run, CONCENTRATE, LITHIUM) == (100.0, 500.0)


def test_one_sampled_minute_cannot_say_what_crossed(a_run, a_sampled_reading):
    run = a_run(tank_readings=(a_sampled_reading(minute=0, weight_g=2100, li_mg_l=50),))

    assert AmountThatCrossed.find_milligrams(run, CONCENTRATE, LITHIUM) is None
    assert AmountThatCrossed.find_ends(run, CONCENTRATE, LITHIUM) is None


def test_a_metal_the_lab_never_reported_cannot_say_what_crossed(a_run, two_sampled_minutes):
    """Magnesium is on these samples; sodium is not, so asking for it gives nothing."""
    run = a_run(tank_readings=two_sampled_minutes)
    sodium = Metal("sodium", "na_mg_l", 22.99, 1)

    assert AmountThatCrossed.find_milligrams(run, CONCENTRATE, sodium) is None


def test_a_run_with_no_readings_at_all_is_not_an_error(a_run):
    assert AmountThatCrossed.find_milligrams(a_run(), CONCENTRATE, LITHIUM) is None


def test_a_tank_nobody_weighs_is_not_an_error(a_run, two_sampled_minutes):
    assert AmountThatCrossed.find_milligrams(a_run(tank_readings=two_sampled_minutes),
                                             "feed", LITHIUM) is None


def test_it_changes_nothing(a_run, two_sampled_minutes):
    run = a_run(tank_readings=two_sampled_minutes)

    AmountThatCrossed.find_milligrams(run, CONCENTRATE, LITHIUM)

    assert [reading.minute for reading in run.tank_readings] == [0, 60]
