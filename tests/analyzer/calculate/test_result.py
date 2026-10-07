"""Result: one run's worked-out numbers, carried as data."""

import pytest

from limodel.analyzer.calculate.result import Result


@pytest.fixture
def result():
    """A result with round numbers, built straight from values."""
    return Result(run_code="AA", cem="GO-10", current_density_ma_cm2=4.5,
                  feed_mg_li_ratio=1.5, permselectivity=0.8, li_recovery_pct=25.0,
                  charge_per_li_offered=1.0, highest_voltage_v=16.0, charge_passed_mah_cm2=0.3,
                  energy_per_mol_li_wh=200.0, li_balance_gap_pct=10.0,
                  mg_balance_gap_pct=12.0)


def test_its_id_is_its_run_code(result):
    assert result.id == "AA"


def test_a_diagnostic_may_be_missing_without_the_rest_minding():
    bare = Result(run_code="BB", cem="Pristine", current_density_ma_cm2=4.0,
                  feed_mg_li_ratio=3.0, permselectivity=0.5, li_recovery_pct=20.0,
                  charge_per_li_offered=1.0, highest_voltage_v=None, charge_passed_mah_cm2=None,
                  energy_per_mol_li_wh=None, li_balance_gap_pct=None,
                  mg_balance_gap_pct=None)

    assert bare.id == "BB"
    assert bare.li_recovery_pct == 20.0


def test_it_cannot_be_changed_after_it_is_worked_out(result):
    with pytest.raises(Exception):
        result.li_recovery_pct = 99.0
