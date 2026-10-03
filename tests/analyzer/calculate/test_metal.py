"""Metal: the two metals the separation is about, each with its column, mass and charge."""

from limodel.analyzer.calculate.metal import LITHIUM, MAGNESIUM


def test_lithium_carries_one_charge_on_an_ion():
    assert LITHIUM.charge == 1


def test_lithium_weighs_6_94_grammes_a_mole():
    assert LITHIUM.g_per_mol == 6.94


def test_lithium_is_read_from_the_li_mg_l_column_of_a_sample():
    assert LITHIUM.field_name == "li_mg_l"


def test_magnesium_carries_two_charges_on_an_ion():
    """Twice lithium's charge, which is what a transport number is a share of."""
    assert MAGNESIUM.charge == 2


def test_magnesium_weighs_24_305_grammes_a_mole():
    assert MAGNESIUM.g_per_mol == 24.305


def test_magnesium_is_read_from_the_mg_mg_l_column_of_a_sample():
    assert MAGNESIUM.field_name == "mg_mg_l"
