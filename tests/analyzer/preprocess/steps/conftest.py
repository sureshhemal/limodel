"""Readings built straight from values: no files, no loader, no journal."""

import pytest

from limodel.models import Run, StackReading, TankReading


def minutes_for(series, minutes):
    """The minutes to put the values at: the ones a test asked for, or every quarter hour."""
    length = len(next(iter(series.values())))

    return minutes or tuple(step * 15 for step in range(length))


@pytest.fixture
def readings():
    """One tank's readings, a value per minute, 15 minutes apart unless told otherwise.

    readings(weight_g=(2119.7, 2117.8, 1800.0)) gives three concentrate readings at
    minutes 0, 15 and 30.
    """
    def build(tank="conc", minutes=None, run_code="AA", **series):
        return [TankReading(run_code=run_code, minute=minute, tank=tank,
                            **{field: values[at] for field, values in series.items()})
                for at, minute in enumerate(minutes_for(series, minutes))]
    return build


@pytest.fixture
def power_readings():
    """A run's power log, a value per minute, 15 minutes apart unless told otherwise.

    power_readings(supply_voltage_v=(11.2, 11.1), meter_voltage_v=(11.18, 1.11)) gives two
    readings of both instruments.
    """
    def build(minutes=None, run_code="AA", **series):
        return [StackReading(run_code=run_code, minute=minute,
                             **{field: values[at] for field, values in series.items()})
                for at, minute in enumerate(minutes_for(series, minutes))]
    return build


@pytest.fixture
def a_run():
    """A run carrying nothing but the readings a test cares about."""
    def build(run_code="AA", tank_readings=(), stack_readings=(), cem="GO-10"):
        return Run(run_code=run_code, series="new_set_mg", run_date="2026-07-09", cem=cem,
                   aem="AR 204", li_feed_mg_l=400, mg_feed_mg_l=2000, conc_start_salt="LiCl",
                   conc_start_g_l=0.5, rinse_salt="Na2SO4", rinse_wt_pct=2, flow_l_min=0.2,
                   area_cm2=6, cell_pairs=10, tare_conc_g=96.2, tare_dil_g=111.5,
                   tare_rinse_g=42, include=True, tank_readings=list(tank_readings),
                   stack_readings=list(stack_readings))
    return build
