"""How much of a metal a tank held at one minute."""

from limodel.analyzer.calculate.quantities.volume_in_a_tank import VolumeInATank


class AmountInATank:
    """The milligrams of a metal in a tank at a minute.

    The lab reports a concentration, which says nothing on its own: the tanks gain and lose
    liquid all run, so only the concentration times the volume can be compared minute to
    minute.
    """

    @staticmethod
    def find_milligrams(reading, tare_g, metal):
        """None when the minute has no sample, no result for this metal, or no weight."""
        if reading.sample is None:
            return None

        mg_per_l = getattr(reading.sample, metal.field_name)
        litres = VolumeInATank.find_litres(reading, tare_g)

        if mg_per_l is None or litres is None:
            return None

        return mg_per_l * litres
