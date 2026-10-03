"""How hard the current was driven through each square centimetre of membrane."""

from statistics import median


class CurrentDensity:
    """The run's usual supply current spread over the membrane area, in mA/cm2.

    The median and not the mean, because a run holds one current all the way through and a
    single misread minute should not move the number that labels the whole run.
    """

    @staticmethod
    def find_ma_per_cm2(run):
        """None when no minute carries a current, or the run has no membrane area."""
        currents = [reading.supply_current_a for reading in run.stack_readings
                    if reading.supply_current_a is not None]

        if not currents or not run.area_cm2:
            return None

        return median(currents) * 1000 / run.area_cm2
