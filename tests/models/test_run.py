"""Run: the one spelling of a membrane, whatever the workbook wrote."""

import pytest

from limodel.models import Run

SETUP = dict(run_code="X", series="made_up", run_date="2026-01-01", aem="AR 204",
             li_feed_mg_l=400, mg_feed_mg_l=2000, conc_start_salt="LiCl", conc_start_g_l=0.5,
             rinse_salt="Na2SO4", rinse_wt_pct=2, flow_l_min=0.2, area_cm2=6, cell_pairs=10,
             tare_conc_g=96.2, tare_dil_g=111.5, tare_rinse_g=42, include=True)


@pytest.mark.parametrize("written", ["GO-10", "GO10", "go10", "Go-10", "go 10", " GO-10 "])
def test_every_way_of_writing_go_10_becomes_one(written):
    assert Run(cem=written, **SETUP).cem == "GO-10"


def test_a_membrane_with_go10_inside_its_name_is_left_alone(written="PDA-GO10/PEI/BT"):
    """It squashes to pdago10peibt, which is its own membrane and not GO-10."""
    assert Run(cem=written, **SETUP).cem == "PDA-GO10/PEI/BT"


@pytest.mark.parametrize("written,meant", [("pristine", "Pristine"),
                                           ("PRISTINE", "Pristine"),
                                           ("pda/pei/15ce/bt", "PDA/PEI/15CE/BT")])
def test_the_other_membranes_are_tidied_the_same_way(written, meant):
    assert Run(cem=written, **SETUP).cem == meant


def test_a_membrane_nobody_has_seen_is_kept_exactly_as_written():
    """Tidying an unknown name risks turning a new membrane into an old one."""
    assert Run(cem="Nafion 117", **SETUP).cem == "Nafion 117"


def test_a_blank_membrane_stays_blank():
    assert Run(cem="", **SETUP).cem == ""
