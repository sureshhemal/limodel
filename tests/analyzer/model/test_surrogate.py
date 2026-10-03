"""Surrogate: every membrane fitted, searched, or reported as one it would not fit."""

from dataclasses import replace

import pytest

from limodel.analyzer.journal import Journal
from limodel.analyzer.model.surrogate import Surrogate


@pytest.fixture
def journal():
    """Empty, as the analyzer hands it over."""
    return Journal()


@pytest.fixture
def a_square(a_result):
    """Four runs of one membrane at 10 and 20 mA/cm2 against 2 and 8 mol/mol.

    Every outcome is a straight line in coded units: permselectivity 2 + x1 + x2/2, recovery
    50 + 10*x1 and voltage 12 + 2*x1, so the best setup can be read off by hand.
    """
    def build(cem="GO-10"):
        corners = ((10.0, 2.0, 0.5, 40.0, 10.0), (20.0, 2.0, 2.5, 60.0, 14.0),
                   (10.0, 8.0, 1.5, 40.0, 10.0), (20.0, 8.0, 3.5, 60.0, 14.0))
        return [a_result(run_code=f"{cem}-{number}", cem=cem, current_density_ma_cm2=current,
                         feed_mg_li_ratio=feed, permselectivity=perm, li_recovery_pct=recovery,
                         highest_voltage_v=voltage)
                for number, (current, feed, perm, recovery, voltage) in enumerate(corners)]
    return build


@pytest.fixture
def current_density_alone(a_result):
    """Five runs of one membrane doubling from 10 to 160 mA/cm2, every one at 2 mol/mol.

    The logs are evenly spaced, so coded x1 is -1, -0.5, 0, 0.5 and 1. Permselectivity is
    2 + x1, recovery 50 + 10*x1 and voltage 12 + 2*x1, all exactly.
    """
    def build(cem="Pristine"):
        runs = ((10.0, 1.0, 40.0, 10.0), (20.0, 1.5, 45.0, 11.0), (40.0, 2.0, 50.0, 12.0),
                (80.0, 2.5, 55.0, 13.0), (160.0, 3.0, 60.0, 14.0))
        return [a_result(run_code=f"{cem}-{number}", cem=cem, current_density_ma_cm2=current,
                         feed_mg_li_ratio=2.0, permselectivity=perm, li_recovery_pct=recovery,
                         highest_voltage_v=voltage)
                for number, (current, perm, recovery, voltage) in enumerate(runs)]
    return build


def test_it_fits_all_three_outcomes_of_a_membrane(journal, a_square):
    models = Surrogate(journal).find_models(a_square())

    assert sorted(models.fits["GO-10"]) == ["highest_voltage_v", "li_recovery_pct",
                                            "permselectivity"]


def test_a_fit_comes_back_as_the_line_the_runs_were_built_from(journal, a_square):
    """40 and 60 percent against coded -1 and 1: a mean of 50 and ten per coded step."""
    models = Surrogate(journal).find_models(a_square())

    assert dict(models.fits["GO-10"]["li_recovery_pct"].find_terms_and_coefficients()) == (
        pytest.approx({"intercept": 50.0, "x1": 10.0}))


def test_the_best_setup_is_the_strongest_current_and_the_highest_feed_ratio(journal, a_square):
    """Permselectivity climbs with both settings, so the top corner of the runs wins."""
    models = Surrogate(journal).find_models(a_square())

    assert models.best_setups["GO-10"].find_settings() == pytest.approx((20.0, 8.0, 1.0))


def test_each_membrane_is_fitted_and_searched_on_its_own(journal, a_square):
    models = Surrogate(journal).find_models(a_square("GO-10") + a_square("Pristine"))

    assert sorted(models.fits) == ["GO-10", "Pristine"]
    assert sorted(models.best_setups) == ["GO-10", "Pristine"]


def test_a_membrane_with_two_runs_is_reported_as_too_few_runs(journal, a_square):
    models = Surrogate(journal).find_models(a_square("GO-10") + a_square("Pristine")[:2])

    assert models.not_fitted == {
        "Pristine": "Pristine has too few runs to fit, 2 against the 3 a fit needs"}


def test_a_membrane_it_will_not_fit_gets_neither_a_fit_nor_a_setup(journal, a_square):
    models = Surrogate(journal).find_models(a_square("GO-10") + a_square("Pristine")[:2])

    assert "Pristine" not in models.fits
    assert "Pristine" not in models.best_setups


def test_a_membrane_whose_settings_never_moved_is_not_fitted(journal, a_result):
    """Three runs at one current density and one feed ratio moved nothing to fit against."""
    given = [a_result(run_code=code, cem="Pristine") for code in ("A", "B", "C")]

    models = Surrogate(journal).find_models(given)

    assert models.not_fitted == {
        "Pristine": "Pristine has no setting that varies across its runs, "
                    "so there is nothing to fit"}


def test_a_membrane_with_a_setting_missing_is_named_for_that(journal, a_result):
    given = [a_result(run_code=code, cem="Pristine", current_density_ma_cm2=current)
             for code, current in (("A", 10.0), ("B", 20.0), ("C", None))]

    models = Surrogate(journal).find_models(given)

    assert models.not_fitted == {
        "Pristine": "Pristine has a run with a setting missing or at zero, "
                    "which has no logarithm"}


def test_a_membrane_that_moved_one_setting_is_still_fitted(journal, current_density_alone):
    """Five runs from 10 to 160 mA/cm2 at one feed ratio: the feed ratio drops out, x1 fits."""
    models = Surrogate(journal).find_models(current_density_alone())

    assert models.not_fitted == {}
    assert models.fits["Pristine"]["permselectivity"].polynomial.term_names == ("intercept",
                                                                                "x1")


def test_the_setting_that_dropped_out_can_be_named_to_a_reader(journal, current_density_alone):
    """The report has to be able to say the fit was made in current density alone."""
    points = Surrogate(journal).find_models(
        current_density_alone()).best_setups["Pristine"].design_points

    assert points.find_kept_settings() == ("current_density_ma_cm2",)
    assert points.find_dropped_settings() == ("feed_mg_li_ratio", "charge_per_li_offered")


def test_the_best_setup_in_one_setting_is_the_strongest_current(journal, current_density_alone):
    """Permselectivity is 2 + x1, so coded 1 wins: 160 mA/cm2 at the 2 mol/mol it was run at."""
    models = Surrogate(journal).find_models(current_density_alone())

    assert models.best_setups["Pristine"].find_settings() == pytest.approx((160.0, 2.0, 1.0))


def test_an_outcome_that_could_not_be_fitted_is_named(journal, a_square):
    """A gap in the voltage leaves the other two fitted and the search with no ceiling."""
    given = a_square()
    given[0] = replace(given[0], highest_voltage_v=None)

    models = Surrogate(journal).find_models(given)

    assert sorted(models.fits["GO-10"]) == ["li_recovery_pct", "permselectivity"]
    assert models.not_fitted == {
        "GO-10": "GO-10 had highest_voltage_v that could not be fitted"}
    assert "GO-10" not in models.best_setups


def test_the_gates_it_is_given_reach_the_search(journal, a_square):
    """A floor of 70 percent is above the 60 the fit offers, so nothing survives it."""
    models = Surrogate(journal, recovery_floor_pct=70.0).find_models(a_square())

    assert models.best_setups["GO-10"].find_settings() is None
    assert models.best_setups["GO-10"].find_refusal() == (
        "nothing inside the measured range cleared the lithium recovery floor")


def test_a_run_naming_no_membrane_is_passed_over(journal, a_square, a_result):
    given = a_square() + [a_result(run_code="ZZ", cem=None)]

    models = Surrogate(journal).find_models(given)

    assert sorted(models.fits) == ["GO-10"]
    assert models.not_fitted == {}


def test_no_results_at_all_is_not_an_error(journal):
    models = Surrogate(journal).find_models([])

    assert (models.fits, models.best_setups, models.not_fitted) == ({}, {}, {})


def test_it_writes_nothing_down(journal, a_square):
    """Everything it reads is already a Result, and a membrane left out is on its answer."""
    Surrogate(journal).find_models(a_square("GO-10") + a_square("Pristine")[:2])

    assert journal.entries == ()
