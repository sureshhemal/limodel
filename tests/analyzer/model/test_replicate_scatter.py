"""ReplicateScatter: how far apart runs repeated at the same setting came out."""

import math

import pytest

from limodel.analyzer.model.replicate_scatter import ReplicateScatter


@pytest.fixture
def scatter():
    """The scatter in lithium recovery, which is the outcome with the hardest gate on it."""
    return ReplicateScatter("li_recovery_pct")


def test_it_says_which_outcome_it_judges(scatter):
    assert scatter.field_name == "li_recovery_pct"


def test_three_runs_at_one_point_spread_by_their_own_distance(scatter, a_result):
    """10, 13 and 16 about a mean of 13: squares 9, 0 and 9 over 2 degrees, so 3."""
    given = [a_result(run_code="AA", li_recovery_pct=10.0),
             a_result(run_code="BB", li_recovery_pct=13.0),
             a_result(run_code="CC", li_recovery_pct=16.0)]

    assert scatter.find_spread(given) == (pytest.approx(3.0), 2)


def test_two_points_that_each_repeat_are_pooled(scatter, a_result):
    """Each pair is 4 apart, so each gives 8, and 16 over 2 degrees makes sqrt(8)."""
    given = [a_result(run_code="AA", current_density_ma_cm2=10.0, li_recovery_pct=10.0),
             a_result(run_code="BB", current_density_ma_cm2=10.0, li_recovery_pct=14.0),
             a_result(run_code="CC", current_density_ma_cm2=20.0, li_recovery_pct=20.0),
             a_result(run_code="DD", current_density_ma_cm2=20.0, li_recovery_pct=24.0)]

    assert scatter.find_spread(given) == (pytest.approx(math.sqrt(8.0)), 2)


def test_each_membrane_keeps_its_own_scatter(scatter, a_result):
    """The lone run on the other membrane must not be read as a third repeat of this point."""
    given = [a_result(run_code="AA", cem="GO-10", li_recovery_pct=10.0),
             a_result(run_code="BB", cem="GO-10", li_recovery_pct=14.0),
             a_result(run_code="CC", cem="GO-20", li_recovery_pct=100.0)]

    assert scatter.find_spread(given) == (pytest.approx(math.sqrt(8.0)), 1)


def test_settings_that_agree_to_two_decimals_are_the_same_point(scatter, a_result):
    """10.001 and 10.004 are one setting the supply could not hold any finer than."""
    given = [a_result(run_code="AA", current_density_ma_cm2=10.001, li_recovery_pct=10.0),
             a_result(run_code="BB", current_density_ma_cm2=10.004, li_recovery_pct=14.0)]

    assert scatter.find_spread(given) == (pytest.approx(math.sqrt(8.0)), 1)


def test_settings_that_differ_by_two_decimals_are_different_points(scatter, a_result):
    given = [a_result(run_code="AA", current_density_ma_cm2=10.004, li_recovery_pct=10.0),
             a_result(run_code="BB", current_density_ma_cm2=10.006, li_recovery_pct=14.0)]

    assert scatter.find_spread(given) is None


def test_a_feed_ratio_apart_is_a_different_point(scatter, a_result):
    given = [a_result(run_code="AA", feed_mg_li_ratio=2.0, li_recovery_pct=10.0),
             a_result(run_code="BB", feed_mg_li_ratio=8.0, li_recovery_pct=14.0)]

    assert scatter.find_spread(given) is None


def test_runs_that_never_repeat_have_no_scatter_to_report(scatter, three_settings):
    assert scatter.find_spread(three_settings()) is None


def test_one_run_on_its_own_has_no_scatter(scatter, a_result):
    assert scatter.find_spread([a_result()]) is None


def test_no_runs_at_all_is_not_an_error(scatter):
    assert scatter.find_spread([]) is None


def test_a_run_missing_the_outcome_is_passed_over(scatter, a_result):
    """The two that are left are still a repeat, so their own distance is still the answer."""
    given = [a_result(run_code="AA", li_recovery_pct=10.0),
             a_result(run_code="BB", li_recovery_pct=None),
             a_result(run_code="CC", li_recovery_pct=14.0)]

    assert scatter.find_spread(given) == (pytest.approx(math.sqrt(8.0)), 1)


def test_a_pair_left_single_by_a_missing_outcome_has_no_scatter(scatter, a_result):
    given = [a_result(run_code="AA", li_recovery_pct=10.0),
             a_result(run_code="BB", li_recovery_pct=None)]

    assert scatter.find_spread(given) is None


def test_a_run_missing_a_setting_cannot_be_placed(scatter, a_result):
    given = [a_result(run_code="AA", li_recovery_pct=10.0),
             a_result(run_code="BB", current_density_ma_cm2=None, li_recovery_pct=14.0)]

    assert scatter.find_spread(given) is None


def test_identical_repeats_have_no_spread_at_all(scatter, a_result):
    """A bench that gave the same number twice reports zero, and that is not a refusal."""
    given = [a_result(run_code="AA", li_recovery_pct=12.0),
             a_result(run_code="BB", li_recovery_pct=12.0)]

    assert scatter.find_spread(given) == (pytest.approx(0.0), 1)


def test_it_serves_any_outcome_it_is_given(a_result):
    """The same rule, set up for the voltage the stack reached."""
    given = [a_result(run_code="AA", highest_voltage_v=10.0),
             a_result(run_code="BB", highest_voltage_v=14.0)]

    assert ReplicateScatter("highest_voltage_v").find_spread(given) == (
        pytest.approx(math.sqrt(8.0)), 1)
