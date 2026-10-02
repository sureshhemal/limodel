"""The supply and the multimeter reading different voltages."""

from limodel.analyzer.preprocess.steps.checks.paired_value_check import PairedValueCheck


class PairedValuesTooFarApart(PairedValueCheck):
    """Rejects the odd one of two voltage readings too far apart.

    The two agree to hundredths of a volt all run, so a gap of a whole volt is one of them
    written down with a digit too many or too few.
    """

    def __init__(self, first, second, label, largest_gap):
        super().__init__(first, second, label)
        self.largest_gap = largest_gap

    def find_worst_offender(self, readings):
        """The widest disagreement over the limit, blaming the instrument unlike itself."""
        judgeable = self.find_judgeable_readings(readings)
        if not judgeable:
            return None

        widest = max(judgeable, key=self._find_gap)
        if self._find_gap(widest) <= self.largest_gap:
            return None

        odd_one = self._find_odd_one(widest, judgeable)

        return widest, odd_one.field_name, (
            f"the two {self.label} readings differ by {self._find_gap(widest):g} "
            f"{odd_one.unit}, and {self._find_reading_text(widest, odd_one)} is unlike its own column")

    def _find_gap(self, reading):
        return abs(self._find_value(reading, self.first) - self._find_value(reading, self.second))
