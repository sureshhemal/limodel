"""A value that cannot happen, whatever the readings around it say."""

from limodel.analyzer.preprocess.steps.checks.check import Check


class ValueOutsideTheRange(Check):
    """Rejects a reading outside the range the experiment can produce.

    This one needs no neighbours: a pH of 0.07 is wrong on its own. It is the only kind of
    rule left when every reading in a series is nonsense.
    """

    def __init__(self, field_name, label, bounds):
        self.field_name = field_name
        self.label = label
        self.low, self.high = bounds

    def find(self, readings):
        """The earliest reading outside the range."""
        for reading in self.judgeable(readings):
            value = getattr(reading, self.field_name)
            if not self.low <= value <= self.high:
                return reading, self.field_name, (
                    f"{self.label} {value:g} is outside {self.low:g} to {self.high:g}")

        return None
