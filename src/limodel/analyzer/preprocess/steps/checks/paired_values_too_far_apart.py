"""The supply and the multimeter reading different voltages."""

from limodel.analyzer.preprocess.steps.checks.paired_value_check import PairedValueCheck


class PairedValuesTooFarApart(PairedValueCheck):
    """Rejects the odd one of two voltage readings that are too far apart.

    The two agree to a few hundredths of a volt all run, so a gap of a whole volt is not
    the instruments differing: it is one of the two written down with a digit too many or
    too few.
    """

    def __init__(self, first, second, label, largest_gap):
        super().__init__(first, second, label)
        self.largest_gap = largest_gap

    def find(self, readings):
        """The widest disagreement over the limit, blaming the instrument unlike itself."""
        judgeable = self.judgeable(readings)
        if not judgeable:
            return None

        widest = max(judgeable, key=self._gap)
        if self._gap(widest) <= self.largest_gap:
            return None

        odd_one = self._the_odd_one(widest, judgeable)

        return widest, odd_one.field_name, (
            f"the two {self.label} readings differ by {self._gap(widest):g} "
            f"{odd_one.unit}, and {self._says(widest, odd_one)} is unlike its own column")

    def _gap(self, reading):
        return abs(self._value(reading, self.first) - self._value(reading, self.second))
