"""LeaveOneOutError: the root mean squared miss on the one row the fit was not shown."""

import math

import pytest

from limodel.analyzer.model.leave_one_out_error import LeaveOneOutError
from limodel.analyzer.model.second_order_polynomial import SecondOrderPolynomial


@pytest.fixture
def a_line():
    """Four points lying exactly on y = 3 + 2*x1."""
    return [(-1.0, 0.0), (0.0, 0.0), (1.0, 0.0), (2.0, 0.0)], [1.0, 3.0, 5.0, 7.0]


def test_a_perfect_fit_misses_the_held_out_row_by_nothing(a_line):
    """Any three of these points give the same line, so the fourth is predicted exactly."""
    rows, outcomes = a_line

    rmse = LeaveOneOutError.find_rmse(SecondOrderPolynomial(("intercept", "x1")), rows, outcomes)

    assert rmse == pytest.approx(0.0)


def test_it_reports_the_root_mean_square_of_the_misses():
    """Outcomes 1, 2, 3 against their mean: the misses are 1.5, 0 and 1.5, so it is sqrt(1.5)."""
    rows = [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]
    mean_only = SecondOrderPolynomial(("intercept",))

    rmse = LeaveOneOutError.find_rmse(mean_only, rows, [1.0, 2.0, 3.0])

    assert rmse == pytest.approx(math.sqrt(1.5))


def test_a_steeper_miss_reports_a_larger_error():
    """Outcomes 0, 2, 10 against their mean: the misses are 6, 3 and 9, so it is sqrt(42)."""
    rows = [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]
    mean_only = SecondOrderPolynomial(("intercept",))

    rmse = LeaveOneOutError.find_rmse(mean_only, rows, [0.0, 2.0, 10.0])

    assert rmse == pytest.approx(math.sqrt(42.0))


def test_a_fold_short_of_rows_is_refused():
    """Two rows leave one behind to fit two terms, which settles nothing."""
    rows = [(-1.0, 0.0), (1.0, 0.0)]

    assert LeaveOneOutError.find_rmse(SecondOrderPolynomial(("intercept", "x1")), rows,
                                      [1.0, 5.0]) is None


def test_one_row_is_refused():
    assert LeaveOneOutError.find_rmse(SecondOrderPolynomial(("intercept",)), [(0.0, 0.0)],
                                      [3.0]) is None


def test_no_rows_at_all_is_refused():
    assert LeaveOneOutError.find_rmse(SecondOrderPolynomial(("intercept",)), [], []) is None


def test_a_missing_outcome_is_refused(a_line):
    rows, _ = a_line

    assert LeaveOneOutError.find_rmse(SecondOrderPolynomial(("intercept", "x1")), rows,
                                      [1.0, None, 5.0, 7.0]) is None


def test_fewer_outcomes_than_rows_is_refused(a_line):
    rows, outcomes = a_line

    assert LeaveOneOutError.find_rmse(SecondOrderPolynomial(("intercept", "x1")), rows,
                                      outcomes[:3]) is None


def test_a_setting_that_never_varies_is_refused():
    rows = [(1.0, 0.0), (1.0, 0.0), (1.0, 0.0), (1.0, 0.0)]

    assert LeaveOneOutError.find_rmse(SecondOrderPolynomial(("intercept", "x1")), rows,
                                      [1.0, 2.0, 3.0, 4.0]) is None
