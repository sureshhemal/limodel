"""Two instruments reading the same thing, held against each other."""

from abc import abstractmethod
from statistics import median

from limodel.analyzer.preprocess.steps.checks.check import Check


class PairedValueCheck(Check):
    """A rule about two instruments reading the same quantity.

    A disagreement does not say which one is wrong; each column's own history does. The
    honest instrument stays near what it has been reading all run. Distances are shares of
    each column's median, so amps and milliamps compare fairly.
    """

    def __init__(self, first, second, label):
        self.first = first        # an Instrument
        self.second = second      # the other Instrument
        self.field_name = first.field_name
        self.label = label        # what the two of them are reading, e.g. "voltage"

    def find_judgeable_readings(self, readings):
        """The readings where both instruments were written down."""
        return [reading for reading in readings
                if self._find_value(reading, self.first) is not None
                and self._find_value(reading, self.second) is not None]

    @abstractmethod
    def find_worst_offender(self, readings):
        """The reading at fault, the value to clear and the reason. Or None."""

    def _find_odd_one(self, reading, judgeable):
        """Which instrument is unlike its own column, as an Instrument."""
        return max((self.first, self.second),
                   key=lambda instrument: self._find_distance_from_usual(reading, instrument, judgeable))

    def _find_distance_from_usual(self, reading, instrument, judgeable):
        """How far this reading sits from what its own instrument usually reads, as a share."""
        usual = median(self._find_value(row, instrument) for row in judgeable)

        return abs(self._find_value(reading, instrument) - usual) / abs(usual) if usual else 0.0

    def _find_reading_text(self, reading, instrument):
        """What that instrument read here, with its own name and unit on it."""
        return f"{instrument.who}'s {self._find_value(reading, instrument):g} {instrument.unit}"

    @staticmethod
    def _find_value(reading, instrument):
        return getattr(reading, instrument.field_name)
