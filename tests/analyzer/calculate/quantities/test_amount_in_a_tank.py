"""AmountInATank: the milligrams of a metal a tank held at one minute."""

from limodel.analyzer.calculate.metal import LITHIUM, MAGNESIUM
from limodel.analyzer.calculate.quantities.amount_in_a_tank import AmountInATank


def test_it_finds_the_milligrams_in_the_tank(a_sampled_reading):
    """50 mg/L in 2.000 L is 100 mg."""
    given = a_sampled_reading(weight_g=2100, li_mg_l=50)

    assert AmountInATank.find_milligrams(given, tare_g=100, metal=LITHIUM) == 100.0


def test_each_metal_is_read_from_its_own_column(a_sampled_reading):
    """100 mg/L of Mg in the same 2.000 L is 200 mg."""
    given = a_sampled_reading(weight_g=2100, li_mg_l=50, mg_mg_l=100)

    assert AmountInATank.find_milligrams(given, tare_g=100, metal=MAGNESIUM) == 200.0


def test_a_minute_that_was_never_sampled_has_no_amount(a_reading):
    assert AmountInATank.find_milligrams(a_reading(weight_g=2100), 100, LITHIUM) is None


def test_a_metal_the_lab_did_not_report_has_no_amount(a_sampled_reading):
    """The lab reports lithium on every sample and magnesium on only some of them."""
    given = a_sampled_reading(weight_g=2100, li_mg_l=50, mg_mg_l=None)

    assert AmountInATank.find_milligrams(given, tare_g=100, metal=MAGNESIUM) is None


def test_a_concentration_without_a_weight_has_no_amount(a_sampled_reading):
    given = a_sampled_reading(weight_g=None, li_mg_l=50)

    assert AmountInATank.find_milligrams(given, tare_g=100, metal=LITHIUM) is None


def test_an_empty_tank_holds_none_of_the_metal(a_sampled_reading):
    given = a_sampled_reading(weight_g=100, li_mg_l=50)

    assert AmountInATank.find_milligrams(given, tare_g=100, metal=LITHIUM) == 0.0
