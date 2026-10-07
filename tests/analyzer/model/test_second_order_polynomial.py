"""SecondOrderPolynomial: a quadratic in the two coded settings, fitted by least squares."""

import pytest

from limodel.analyzer.model.second_order_polynomial import (SecondOrderPolynomial,
                                                            find_term_names)

TERMS_IN_ORDER = find_term_names(2)


@pytest.fixture
def a_line():
    """Three points lying exactly on y = 3 + 2*x1."""
    return [(-1.0, 0.0), (0.0, 0.0), (1.0, 0.0)], [1.0, 3.0, 5.0]


def test_the_interaction_is_never_a_term():
    """Left out on purpose: the runs give an x1 by x2 term nothing to be fitted to."""
    assert find_term_names(2) == ("intercept", "x1", "x2", "x1_squared", "x2_squared")
    assert find_term_names(3) == ("intercept", "x1", "x2", "x3",
                                 "x1_squared", "x2_squared", "x3_squared")


def test_it_says_which_terms_it_may_use():
    assert SecondOrderPolynomial(("intercept", "x1")).term_names == ("intercept", "x1")


def test_points_on_a_line_give_back_the_line(a_line):
    rows, outcomes = a_line

    fit = SecondOrderPolynomial(("intercept", "x1")).find_fit(rows, outcomes)

    assert fit.coefficients == pytest.approx((3.0, 2.0))


def test_points_on_a_parabola_give_back_the_parabola():
    """y = 2 + 3*x1 + 4*x1^2, which reads 3, 2 and 9 at x1 of -1, 0 and 1."""
    rows = [(-1.0, 0.0), (0.0, 0.0), (1.0, 0.0)]

    fit = SecondOrderPolynomial(("intercept", "x1", "x1_squared")).find_fit(rows, [3.0, 2.0, 9.0])

    assert fit.coefficients == pytest.approx((2.0, 3.0, 4.0))


def test_all_five_terms_come_back_exact_from_five_points():
    """y = 1 + 2*x1 + 3*x2 + 4*x1^2 + 5*x2^2 read at the centre and the four axis points."""
    rows = [(0.0, 0.0), (1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)]
    outcomes = [1.0, 7.0, 3.0, 9.0, 3.0]

    fit = SecondOrderPolynomial(TERMS_IN_ORDER).find_fit(rows, outcomes)

    assert fit.coefficients == pytest.approx((1.0, 2.0, 3.0, 4.0, 5.0))


def test_it_predicts_a_point_it_was_never_fitted_at(a_line):
    rows, outcomes = a_line

    fit = SecondOrderPolynomial(("intercept", "x1")).find_fit(rows, outcomes)

    assert fit.find_prediction((2.0, 0.0)) == pytest.approx(7.0)


def test_it_names_each_coefficient_so_the_equation_can_be_printed(a_line):
    rows, outcomes = a_line

    fit = SecondOrderPolynomial(("intercept", "x1")).find_fit(rows, outcomes)

    assert fit.find_terms_and_coefficients() == (("intercept", pytest.approx(3.0)),
                                                 ("x1", pytest.approx(2.0)))


def test_fitting_leaves_the_polynomial_it_was_asked_of_unfitted(a_line):
    rows, outcomes = a_line
    terms = SecondOrderPolynomial(("intercept", "x1"))

    terms.find_fit(rows, outcomes)

    assert terms.coefficients is None


def test_an_unfitted_polynomial_predicts_nothing():
    assert SecondOrderPolynomial(("intercept", "x1")).find_prediction((0.0, 0.0)) is None


def test_an_unfitted_polynomial_has_no_equation_to_print():
    assert SecondOrderPolynomial(("intercept", "x1")).find_terms_and_coefficients() is None


def test_fewer_rows_than_terms_is_not_fitted():
    """Two runs cannot settle three coefficients, however well they would seem to fit."""
    rows = [(-1.0, 0.0), (1.0, 0.0)]
    terms = SecondOrderPolynomial(("intercept", "x1", "x1_squared"))

    assert terms.find_fit(rows, [1.0, 5.0]) is None


def test_one_row_is_not_fitted():
    assert SecondOrderPolynomial(("intercept", "x1")).find_fit([(0.0, 0.0)], [3.0]) is None


def test_no_rows_at_all_is_not_fitted():
    assert SecondOrderPolynomial(("intercept", "x1")).find_fit([], []) is None


def test_a_setting_that_never_varies_is_not_fitted():
    """With x1 the same everywhere it moves with the intercept, and neither can be told apart."""
    rows = [(1.0, 0.0), (1.0, 0.0), (1.0, 0.0)]

    assert SecondOrderPolynomial(("intercept", "x1")).find_fit(rows, [1.0, 2.0, 3.0]) is None


def test_a_missing_outcome_is_not_fitted(a_line):
    rows, _ = a_line

    assert SecondOrderPolynomial(("intercept", "x1")).find_fit(rows, [1.0, None, 5.0]) is None


def test_a_missing_coded_setting_is_not_fitted():
    rows = [(-1.0, 0.0), (None, 0.0), (1.0, 0.0)]

    assert SecondOrderPolynomial(("intercept", "x1")).find_fit(rows, [1.0, 3.0, 5.0]) is None


def test_more_outcomes_than_rows_is_not_fitted(a_line):
    rows, outcomes = a_line

    assert SecondOrderPolynomial(("intercept", "x1")).find_fit(rows, outcomes + [9.0]) is None


def test_a_term_it_does_not_know_is_not_fitted(a_line):
    rows, outcomes = a_line

    assert SecondOrderPolynomial(("intercept", "x1_x2")).find_fit(rows, outcomes) is None
