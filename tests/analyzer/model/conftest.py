"""Results built straight from values: no files, no loader, no workbook.

The settings double from one run to the next, so their logs are evenly spaced and the coded
values come out as exactly -1, 0 and 1.
"""

import pytest

from limodel.analyzer.calculate.result import Result


@pytest.fixture
def a_result():
    """One run, carrying only the membrane, the two settings and the outcomes."""
    def build(run_code="AA", cem="GO-10", current_density_ma_cm2=10.0, feed_mg_li_ratio=2.0,
              permselectivity=1.0, li_recovery_pct=50.0, highest_voltage_v=12.0,
              charge_per_li_offered=1.0):
        return Result(run_code=run_code, cem=cem,
                      current_density_ma_cm2=current_density_ma_cm2,
                      feed_mg_li_ratio=feed_mg_li_ratio,
                      charge_per_li_offered=charge_per_li_offered,
                      permselectivity=permselectivity, li_recovery_pct=li_recovery_pct,
                      highest_voltage_v=highest_voltage_v, charge_passed_mah_cm2=None,
                      energy_per_mol_li_wh=None, li_balance_gap_pct=None,
                      mg_balance_gap_pct=None)
    return build


@pytest.fixture
def three_settings(a_result):
    """Runs at 10, 20 and 40 mA/cm2, against 2, 4 and 8 mol/mol, pushed to 1, 2 and 4.

    Every setting doubles with the next run, so all three code to -1, 0 and +1 together.
    """
    def build():
        return [a_result(run_code="AA", current_density_ma_cm2=10.0, feed_mg_li_ratio=2.0,
                         charge_per_li_offered=1.0),
                a_result(run_code="BB", current_density_ma_cm2=20.0, feed_mg_li_ratio=4.0,
                         charge_per_li_offered=2.0),
                a_result(run_code="CC", current_density_ma_cm2=40.0, feed_mg_li_ratio=8.0,
                         charge_per_li_offered=4.0)]
    return build
