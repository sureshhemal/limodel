"""VolumeInATank: the litres in a tank, read off the balance."""

from limodel.analyzer.calculate.quantities.volume_in_a_tank import VolumeInATank


def test_it_finds_the_litres_a_weight_stands_for(a_reading):
    """2100 g on the balance less a 100 g tare is 2000 g of liquid, so 2.000 L."""
    assert VolumeInATank.find_litres(a_reading(weight_g=2100), tare_g=100) == 2.0


def test_a_tank_at_its_tare_holds_nothing(a_reading):
    assert VolumeInATank.find_litres(a_reading(weight_g=100), tare_g=100) == 0.0


def test_a_reading_without_a_weight_has_no_volume(a_reading):
    assert VolumeInATank.find_litres(a_reading(weight_g=None), tare_g=100) is None


def test_a_tank_without_a_tare_has_no_volume(a_reading):
    assert VolumeInATank.find_litres(a_reading(weight_g=2100), tare_g=None) is None


def test_a_weight_under_the_tare_is_reported_as_it_reads(a_reading):
    """A negative volume is impossible, so it is left showing rather than tidied away."""
    assert VolumeInATank.find_litres(a_reading(weight_g=50), tare_g=100) == -0.05


def test_it_changes_nothing(a_reading):
    given = a_reading(weight_g=2100)

    VolumeInATank.find_litres(given, tare_g=100)

    assert given.weight_g == 2100
