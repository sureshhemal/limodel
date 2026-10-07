"""DesignPoints: every setting of every run in coded units, and the way back."""

import pytest

from limodel.analyzer.model.design_points import DesignPoints

CURRENT_DENSITY = "current_density_ma_cm2"
FEED_RATIO = "feed_mg_li_ratio"
CHARGE_PER_LI = "charge_per_li_offered"


@pytest.fixture
def current_density_alone(a_result):
    """Runs at 10 and 40 mA/cm2, both of them at 2 mol/mol, so only one setting moves."""
    def build():
        return [a_result(run_code="AA", current_density_ma_cm2=10.0, feed_mg_li_ratio=2.0),
                a_result(run_code="BB", current_density_ma_cm2=40.0, feed_mg_li_ratio=2.0)]
    return build


@pytest.fixture
def one_setting_twice(a_result):
    """Two runs at the very same setting, so neither column moves."""
    def build():
        return [a_result(run_code="AA", current_density_ma_cm2=10.0, feed_mg_li_ratio=2.0),
                a_result(run_code="BB", current_density_ma_cm2=10.0, feed_mg_li_ratio=2.0)]
    return build


def test_the_lowest_run_sits_at_minus_one(three_settings):
    """10 mA/cm2 and 2 mol/mol are the lowest of the three, so both code to -1."""
    assert DesignPoints(three_settings()).find_coded_rows()[0] == pytest.approx((-1.0, -1.0, -1.0))


def test_the_middle_run_sits_at_zero(three_settings):
    """20 is the geometric middle of 10 and 40, and 4 of 2 and 8, so the logs centre there."""
    assert DesignPoints(three_settings()).find_coded_rows()[1] == pytest.approx((0.0, 0.0, 0.0))


def test_the_highest_run_sits_at_plus_one(three_settings):
    assert DesignPoints(three_settings()).find_coded_rows()[2] == pytest.approx((1.0, 1.0, 1.0))


def test_it_codes_one_row_per_run(three_settings):
    assert len(DesignPoints(three_settings()).find_coded_rows()) == 3


def test_every_setting_is_kept_when_every_one_of_them_moves(three_settings):
    points = DesignPoints(three_settings())

    assert points.find_kept_settings() == (CURRENT_DENSITY, FEED_RATIO, CHARGE_PER_LI)
    assert points.find_dropped_settings() == ()


def test_every_coded_setting_is_usable_when_every_one_of_them_moves(three_settings):
    assert DesignPoints(three_settings()).find_usable_coded_names() == ("x1", "x2", "x3")


def test_the_centre_of_the_coded_box_is_the_middle_run(three_settings):
    points = DesignPoints(three_settings())

    assert points.find_real_from_coded((0.0, 0.0, 0.0)) == pytest.approx((20.0, 4.0, 2.0))


def test_a_corner_of_the_coded_box_is_a_setting_never_run(three_settings):
    """Highest current against the lowest feed and the gentlest push, which no run was."""
    points = DesignPoints(three_settings())

    assert points.find_real_from_coded((1.0, -1.0, -1.0)) == pytest.approx((40.0, 2.0, 1.0))


def test_a_real_setting_codes_back_to_where_it_came_from(three_settings):
    points = DesignPoints(three_settings())

    assert points.find_coded_from_real((40.0, 2.0, 1.0)) == pytest.approx((1.0, -1.0, -1.0))


def test_a_setting_outside_the_runs_codes_past_the_edge(three_settings):
    """80 mA/cm2 is one more doubling past 40, so it lands at 2 in coded units."""
    points = DesignPoints(three_settings())

    assert points.find_coded_from_real((80.0, 4.0, 2.0)) == pytest.approx((2.0, 0.0, 0.0))


def test_a_setting_held_at_one_value_is_dropped_and_the_one_that_moves_still_codes(
        current_density_alone):
    """10 and 40 mA/cm2 code to -1 and 1; the feed ratio moved nothing, so it sits at 0."""
    rows = DesignPoints(current_density_alone()).find_coded_rows()

    assert rows[0] == pytest.approx((-1.0, 0.0, 0.0))
    assert rows[1] == pytest.approx((1.0, 0.0, 0.0))


def test_it_names_the_setting_it_kept_and_the_one_it_dropped(current_density_alone):
    points = DesignPoints(current_density_alone())

    assert points.find_kept_settings() == (CURRENT_DENSITY,)
    assert points.find_dropped_settings() == (FEED_RATIO, CHARGE_PER_LI)


def test_only_the_setting_that_moved_is_usable_as_a_coded_name(current_density_alone):
    assert DesignPoints(current_density_alone()).find_usable_coded_names() == ("x1",)


def test_a_dropped_setting_reads_back_as_the_one_value_it_was_held_at(current_density_alone):
    """Coded 1 in current density is 40 mA/cm2; the other two never moved off their value."""
    points = DesignPoints(current_density_alone())

    assert points.find_real_from_coded((1.0, 0.0, 0.0)) == pytest.approx((40.0, 2.0, 1.0))


def test_a_dropped_setting_reads_back_the_same_whatever_coded_value_it_is_offered(
        current_density_alone):
    """The search sweeps -1..1 in both, and in a dropped setting every level is 2 mol/mol."""
    points = DesignPoints(current_density_alone())

    assert points.find_real_from_coded((1.0, 1.0, 1.0)) == pytest.approx((40.0, 2.0, 1.0))
    assert points.find_real_from_coded((1.0, -1.0, -1.0)) == pytest.approx((40.0, 2.0, 1.0))


def test_runs_with_no_setting_that_varies_cannot_be_coded(one_setting_twice):
    """Two runs at 10 mA/cm2 and 2 mol/mol move nothing, so there is no design to code."""
    assert DesignPoints(one_setting_twice()).find_coded_rows() is None


def test_runs_with_no_setting_that_varies_have_nothing_kept_and_nothing_dropped(
        one_setting_twice):
    points = DesignPoints(one_setting_twice())

    assert points.find_kept_settings() is None
    assert points.find_dropped_settings() is None
    assert points.find_usable_coded_names() is None


def test_a_missing_setting_cannot_be_coded(a_result, three_settings):
    given = three_settings() + [a_result(run_code="DD", current_density_ma_cm2=None)]

    assert DesignPoints(given).find_coded_rows() is None


def test_a_setting_of_zero_has_no_logarithm(a_result, three_settings):
    given = three_settings() + [a_result(run_code="DD", current_density_ma_cm2=0.0)]

    assert DesignPoints(given).find_coded_rows() is None


def test_one_run_on_its_own_cannot_be_coded(a_result):
    """A single run is its own lowest and highest in both settings, so nothing varies."""
    assert DesignPoints([a_result()]).find_coded_rows() is None


def test_no_runs_at_all_cannot_be_coded():
    assert DesignPoints([]).find_coded_rows() is None


def test_no_runs_at_all_cannot_be_turned_back_into_real_units():
    assert DesignPoints([]).find_real_from_coded((0.0, 0.0, 0.0)) is None


def test_a_coded_point_of_the_wrong_width_is_refused(three_settings):
    assert DesignPoints(three_settings()).find_real_from_coded((0.0,)) is None


def test_a_real_point_of_the_wrong_width_is_refused(three_settings):
    assert DesignPoints(three_settings()).find_coded_from_real((20.0, 4.0)) is None
