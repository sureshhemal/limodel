"""The supply and the multimeter reading currents that do not match."""

from limodel.analyzer.preprocess.steps.checks.paired_value_check import PairedValueCheck


class PairedValuesOutOfProportion(PairedValueCheck):
    """Rejects the odd one of two current readings whose ratio is wrong.

    The supply reads about a seventh higher than the multimeter throughout, so the two are
    compared as a ratio rather than by subtracting. A ratio outside the band means a digit
    went wrong, not that the instruments drifted.
    """

    def __init__(self, first, second, label, band, scale):
        super().__init__(first, second, label)
        self.low, self.high = band
        self.scale = scale   # what to multiply the first reading by to match the other's unit

    def find(self, readings):
        """The worst ratio outside the band, blaming the instrument unlike itself."""
        judgeable = [reading for reading in self.judgeable(readings)
                     if self._value(reading, self.second)]
        outside = [reading for reading in judgeable
                   if not self.low <= self._ratio(reading) <= self.high]
        if not outside:
            return None

        worst = max(outside, key=lambda reading: abs(self._ratio(reading) - 1))
        odd_one = self._the_odd_one(worst, judgeable)

        return worst, odd_one.field_name, (
            f"the two {self.label} readings are {self._ratio(worst):.3g} times apart, "
            f"outside {self.low:g} to {self.high:g}, and {self._says(worst, odd_one)} is "
            f"the odd one")

    def _ratio(self, reading):
        return self._value(reading, self.first) * self.scale / self._value(reading, self.second)
