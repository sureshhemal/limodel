"""How much liquid a tank held at one minute."""

from limodel.analyzer.calculate.constants import SOLUTION_G_PER_L


class VolumeInATank:
    """The litres in a tank, read off the balance.

    Nothing measured the volume directly: the tank sat on a balance all run, so the liquid
    is whatever the balance read less the weight of the empty tank.
    """

    @staticmethod
    def find_litres(reading, tare_g):
        """None when the balance gave nothing for this minute."""
        if reading.weight_g is None or tare_g is None:
            return None

        return (reading.weight_g - tare_g) / SOLUTION_G_PER_L
