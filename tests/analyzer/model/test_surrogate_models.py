"""SurrogateModels: the fits, the best setups and the refusals, carried as one answer."""

import pytest

from limodel.analyzer.model.surrogate_models import SurrogateModels

A_FIT = "the permselectivity of GO-10, fitted"
A_BEST_SETUP = "the setup GO-10 allows"
A_REFUSAL = "Pristine has too few runs to fit, 2 against the 3 a fit needs"


@pytest.fixture
def models():
    """One membrane fitted and searched, one it would not fit, built straight from values."""
    return SurrogateModels(fits={"GO-10": {"permselectivity": A_FIT}},
                           best_setups={"GO-10": A_BEST_SETUP},
                           not_fitted={"Pristine": A_REFUSAL})


def test_a_fit_is_found_under_its_membrane_and_then_its_outcome(models):
    assert models.fits["GO-10"]["permselectivity"] == A_FIT


def test_a_best_setup_is_found_under_the_membrane_it_belongs_to(models):
    assert models.best_setups["GO-10"] == A_BEST_SETUP


def test_a_membrane_it_would_not_fit_carries_the_reason_beside_it(models):
    assert models.not_fitted["Pristine"] == A_REFUSAL


def test_a_membrane_that_was_fitted_is_not_among_the_refusals(models):
    assert "GO-10" not in models.not_fitted


def test_a_membrane_it_would_not_fit_has_neither_a_fit_nor_a_setup(models):
    assert "Pristine" not in models.fits
    assert "Pristine" not in models.best_setups


def test_nothing_fitted_at_all_is_three_empty_dicts():
    models = SurrogateModels(fits={}, best_setups={}, not_fitted={})

    assert (models.fits, models.best_setups, models.not_fitted) == ({}, {}, {})


def test_it_cannot_be_changed_once_the_fitting_has_handed_it_over(models):
    with pytest.raises(Exception):
        models.fits = {}
