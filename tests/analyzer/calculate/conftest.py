"""Runs, readings and samples built straight from values: no files, no loader, no workbook.

The weights here are tare 100 g plus a round number of litres, and the concentrations are
round, so every expected milligram in these tests is exact and can be checked in the head.
"""

import pytest

from limodel.analyzer.calculate.constants import CONCENTRATE
from limodel.models import Run, Sample, StackReading, TankReading


@pytest.fixture
def a_reading():
    """One tank reading, with nothing on it but a weight."""
    def build(tank=CONCENTRATE, minute=0, weight_g=None, run_code="AA"):
        return TankReading(run_code=run_code, minute=minute, tank=tank, weight_g=weight_g)
    return build


@pytest.fixture
def a_sampled_reading():
    """One tank reading with a lab sample on it, which is what a metal amount needs.

    a_sampled_reading(minute=0, weight_g=2100, li_mg_l=50) is 2.000 L holding 100 mg of Li.
    """
    def build(tank=CONCENTRATE, minute=0, weight_g=None, li_mg_l=None, mg_mg_l=None,
              run_code="AA"):
        sample = Sample(sample_id=f"{run_code}-{tank}-{minute}", run_code=run_code,
                        minute=minute, tank=tank, li_mg_l=li_mg_l, mg_mg_l=mg_mg_l)

        return TankReading(run_code=run_code, minute=minute, tank=tank, weight_g=weight_g,
                           sample=sample)
    return build


@pytest.fixture
def a_run():
    """A run carrying round tares and only the readings a test cares about."""
    def build(run_code="AA", tank_readings=(), stack_readings=(), tare_conc_g=100.0,
              tare_dil_g=100.0, tare_rinse_g=100.0, li_feed_mg_l=400.0, mg_feed_mg_l=2000.0,
              area_cm2=10.0, include=True):
        return Run(run_code=run_code, series="new_set_mg", run_date="2026-07-09", cem="GO-10",
                   aem="AR 204", li_feed_mg_l=li_feed_mg_l, mg_feed_mg_l=mg_feed_mg_l,
                   conc_start_salt="LiCl", conc_start_g_l=0.5, rinse_salt="Na2SO4",
                   rinse_wt_pct=2, flow_l_min=0.2, area_cm2=area_cm2, cell_pairs=10,
                   tare_conc_g=tare_conc_g, tare_dil_g=tare_dil_g, tare_rinse_g=tare_rinse_g,
                   include=include, tank_readings=list(tank_readings),
                   stack_readings=list(stack_readings))
    return build


@pytest.fixture
def a_stack_reading():
    """One minute of the power log."""
    def build(minute=0, supply_voltage_v=None, supply_current_a=None, run_code="AA"):
        return StackReading(run_code=run_code, minute=minute,
                            supply_voltage_v=supply_voltage_v,
                            supply_current_a=supply_current_a)
    return build
