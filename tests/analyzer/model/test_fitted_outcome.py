"""FittedOutcome: one outcome of one membrane, with the terms that earned their place."""

import pytest

from limodel.analyzer.model.fitted_outcome import CANDIDATE_TERMS, FittedOutcome


@pytest.fixture
def a_square(a_result):
    """Four runs at 10 and 20 mA/cm2 against 2 and 8 mol/mol, so coded x1 and x2 are -1 and 1.

    Recovery is 50 + 10*x1 and permselectivity is 2 + x1 + x2/2, both exactly, so what a fit
    should come back with can be read straight off the values.
    """
    def build(li_recovery_pct=(40.0, 60.0, 40.0, 60.0),
              permselectivity=(0.5, 2.5, 1.5, 3.5)):
        corners = ((10.0, 2.0), (20.0, 2.0), (10.0, 8.0), (20.0, 8.0))
        return [a_result(run_code=code, current_density_ma_cm2=current, feed_mg_li_ratio=feed,
                         permselectivity=perm, li_recovery_pct=recovery)
                for code, (current, feed), perm, recovery
                in zip("ABCD", corners, permselectivity, li_recovery_pct)]
    return build


@pytest.fixture
def current_density_alone(a_result):
    """Five runs doubling from 10 to 160 mA/cm2, every one at 2 mol/mol.

    The logs are evenly spaced, so coded x1 is -1, -0.5, 0, 0.5 and 1, and the feed ratio
    moved nothing at all.
    """
    def build(li_recovery_pct=(40.0, 45.0, 50.0, 55.0, 60.0)):
        currents = (10.0, 20.0, 40.0, 80.0, 160.0)
        return [a_result(run_code=code, current_density_ma_cm2=current, feed_mg_li_ratio=2.0,
                         li_recovery_pct=recovery)
                for code, current, recovery in zip("ABCDE", currents, li_recovery_pct)]
    return build


def test_it_says_which_membrane_and_which_outcome_it_is(a_square):
    fit = FittedOutcome.find_fit("GO-10", "li_recovery_pct", a_square())

    assert (fit.cem, fit.field_name) == ("GO-10", "li_recovery_pct")


def test_a_straight_line_comes_back_as_the_line_it_was_built_from(a_square):
    """40 and 60 against coded -1 and 1: a mean of 50 and ten percent per coded step."""
    fit = FittedOutcome.find_fit("GO-10", "li_recovery_pct", a_square())

    assert dict(fit.find_terms_and_coefficients()) == pytest.approx({"intercept": 50.0,
                                                                     "x1": 10.0})


def test_it_keeps_only_the_setting_the_outcome_moves_with(a_square):
    """Recovery does not move with the feed ratio, so x2 cannot better an error of nothing."""
    fit = FittedOutcome.find_fit("GO-10", "li_recovery_pct", a_square())

    assert fit.polynomial.term_names == ("intercept", "x1")


def test_the_second_candidate_is_reached_when_the_first_one_does_not_help(a_square):
    """Recovery is 50 + 10*x2 here: x1 moves it not at all and x2 moves it all of it.

    x1 is offered first and makes the error worse, which must not end the search, because x2
    behind it is the term the runs actually carry.
    """
    given = a_square(li_recovery_pct=(40.0, 40.0, 60.0, 60.0))

    fit = FittedOutcome.find_fit("GO-10", "li_recovery_pct", given)

    assert fit.polynomial.term_names == ("intercept", "x2")
    assert dict(fit.find_terms_and_coefficients()) == pytest.approx({"intercept": 50.0,
                                                                     "x2": 10.0})


def test_a_term_that_lowers_the_error_is_kept(a_square):
    """Permselectivity moves with both settings, so x2 earns a place and x1 squared cannot."""
    fit = FittedOutcome.find_fit("GO-10", "permselectivity", a_square())

    assert fit.polynomial.term_names == ("intercept", "x1", "x2")
    assert dict(fit.find_terms_and_coefficients()) == pytest.approx({"intercept": 2.0,
                                                                     "x1": 1.0, "x2": 0.5})


def test_a_squared_term_is_not_offered_until_its_own_linear_term_is_in():
    """From the intercept alone only the two slopes are on offer, neither squared term."""
    assert FittedOutcome.find_terms_it_may_add(("intercept",)) == ("x1", "x2", "x3")


def test_a_squared_term_is_offered_once_its_own_linear_term_is_in():
    """x1 is in, so x1 squared may follow it; x2 squared still has to wait for x2."""
    assert FittedOutcome.find_terms_it_may_add(("intercept", "x1")) == ("x2", "x3", "x1_squared")


def test_a_curve_with_no_slope_under_it_stays_at_the_mean(current_density_alone):
    """Recovery is 50 + 10*x1 squared: 60, 52.5, 50, 52.5 and 60, symmetric about the middle.

    x1 cannot lower the error of a symmetric curve, so x1 squared never comes up for a place
    and the fit is the mean of the five, 275 over 5.
    """
    given = current_density_alone(li_recovery_pct=(60.0, 52.5, 50.0, 52.5, 60.0))

    fit = FittedOutcome.find_fit("GO-10", "li_recovery_pct", given)

    assert fit.polynomial.term_names == ("intercept",)
    assert dict(fit.find_terms_and_coefficients()) == pytest.approx({"intercept": 55.0})


def test_a_setting_held_at_one_value_is_fitted_around_not_refused(current_density_alone):
    """Recovery is 50 + 10*x1 across five runs at one feed ratio, so x1 alone carries it."""
    fit = FittedOutcome.find_fit("GO-10", "li_recovery_pct", current_density_alone())

    assert fit.polynomial.term_names == ("intercept", "x1")
    assert dict(fit.find_terms_and_coefficients()) == pytest.approx({"intercept": 50.0,
                                                                     "x1": 10.0})


def test_a_curve_in_the_only_setting_that_moved_keeps_both_terms(current_density_alone):
    """Recovery is 50 + 10*x1 + 10*x1 squared: 50, 47.5, 50, 57.5 and 70.

    The slope earns its place first and the curve on top of it then fits the five exactly.
    """
    given = current_density_alone(li_recovery_pct=(50.0, 47.5, 50.0, 57.5, 70.0))

    fit = FittedOutcome.find_fit("GO-10", "li_recovery_pct", given)

    assert fit.polynomial.term_names == ("intercept", "x1", "x1_squared")
    assert dict(fit.find_terms_and_coefficients()) == pytest.approx({"intercept": 50.0,
                                                                     "x1": 10.0,
                                                                     "x1_squared": 10.0})


def test_a_term_built_on_a_dropped_setting_is_never_a_candidate(current_density_alone):
    """The feed ratio moved nothing across these runs, so x2 and x2 squared are not offered."""
    assert FittedOutcome.find_candidates_on(("x1",)) == ("x1", "x1_squared")


def test_an_interaction_between_settings_is_never_a_candidate():
    """The runs give it no support, so it is left off the list on purpose."""
    assert CANDIDATE_TERMS == ("x1", "x2", "x3", "x1_squared", "x2_squared", "x3_squared")
    assert not [name for name in CANDIDATE_TERMS if "*" in name]


def test_an_interaction_is_left_out_however_well_it_would_fit(a_square):
    """Permselectivity is 2 + x1*x2 here: 3, 1, 1 and 3, which x1*x2 would fit exactly.

    Neither slope on its own lowers the error of that, and there is no interaction to offer,
    so the honest answer is the mean of the four.
    """
    given = a_square(permselectivity=(3.0, 1.0, 1.0, 3.0))

    fit = FittedOutcome.find_fit("GO-10", "permselectivity", given)

    assert fit.polynomial.term_names == ("intercept",)
    assert dict(fit.find_terms_and_coefficients()) == pytest.approx({"intercept": 2.0})


def test_a_fit_that_passes_through_every_run_misses_the_held_out_one_by_nothing(a_square):
    fit = FittedOutcome.find_fit("GO-10", "li_recovery_pct", a_square())

    assert fit.leave_one_out_rmse == pytest.approx(0.0)


def test_it_predicts_what_its_coefficients_say(a_square):
    """50 + 10*x1 at the strongest current the runs covered."""
    fit = FittedOutcome.find_fit("GO-10", "li_recovery_pct", a_square())

    assert fit.find_prediction((1.0, 1.0)) == pytest.approx(60.0)


def test_runs_repeated_at_one_setting_are_the_yardstick_it_carries(a_result, a_square):
    """A second run at 10 mA/cm2 reading 44 against the first one's 40: 8 over 1 degree."""
    given = a_square() + [a_result(run_code="E", current_density_ma_cm2=10.0,
                                   feed_mg_li_ratio=2.0, li_recovery_pct=44.0)]

    fit = FittedOutcome.find_fit("GO-10", "li_recovery_pct", given)

    assert fit.replicate_spread == (pytest.approx(8.0 ** 0.5), 1)


def test_runs_that_never_repeat_leave_it_without_a_yardstick(a_square):
    fit = FittedOutcome.find_fit("GO-10", "li_recovery_pct", a_square())

    assert fit.replicate_spread is None


def test_two_runs_can_only_give_their_mean(a_result):
    """Each fold is one run, so each predicts the other: 40 and 60 miss by 20 either way."""
    given = [a_result(run_code="A", current_density_ma_cm2=10.0, feed_mg_li_ratio=2.0,
                      li_recovery_pct=40.0),
             a_result(run_code="B", current_density_ma_cm2=20.0, feed_mg_li_ratio=8.0,
                      li_recovery_pct=60.0)]

    fit = FittedOutcome.find_fit("GO-10", "li_recovery_pct", given)

    assert fit.polynomial.term_names == ("intercept",)
    assert fit.leave_one_out_rmse == pytest.approx(20.0)


def test_a_missing_outcome_cannot_be_fitted_around(a_square):
    given = a_square(li_recovery_pct=(40.0, 60.0, None, 60.0))

    assert FittedOutcome.find_fit("GO-10", "li_recovery_pct", given) is None


def test_an_outcome_the_runs_do_not_carry_cannot_be_fitted(a_square):
    assert FittedOutcome.find_fit("GO-10", "nothing_measured", a_square()) is None


def test_one_run_is_too_few_to_fit(a_result):
    assert FittedOutcome.find_fit("GO-10", "li_recovery_pct", [a_result()]) is None


def test_no_runs_at_all_is_not_an_error():
    assert FittedOutcome.find_fit("GO-10", "li_recovery_pct", []) is None


def test_runs_with_no_setting_that_varies_cannot_be_fitted(a_result):
    """Three runs at one current density and one feed ratio moved nothing to fit against."""
    given = [a_result(run_code=code, current_density_ma_cm2=10.0, feed_mg_li_ratio=2.0,
                      li_recovery_pct=recovery)
             for code, recovery in (("A", 40.0), ("B", 60.0), ("C", 70.0))]

    assert FittedOutcome.find_fit("GO-10", "li_recovery_pct", given) is None
