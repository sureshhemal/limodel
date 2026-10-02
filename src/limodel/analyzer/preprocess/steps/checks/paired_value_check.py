"""Two instruments reading the same thing, held against each other."""

from abc import abstractmethod
from statistics import median

from limodel.analyzer.preprocess.steps.checks.check import Check


class PairedValueCheck(Check):
    """A rule about a pair of readings taken of the same quantity by two instruments.

    A disagreement says something is wrong but not which instrument is wrong, so the pair
    alone cannot settle it. What settles it is each column's own history: the honest
    instrument stays near what it has been reading all run, and the one that lost or gained
    a digit does not. Only that one is cleared, because the other value is good.

    Distances are measured as a share of each column's own median, so a supply reading in
    amps and a meter reading in milliamps can be compared fairly.
    """

    def __init__(self, first, second, label):
        self.first = first        # an Instrument
        self.second = second      # the other Instrument
        self.field_name = first.field_name
        self.label = label        # what the two of them are reading, e.g. "voltage"

    def judgeable(self, readings):
        """The readings where both instruments were written down."""
        return [reading for reading in readings
                if self._value(reading, self.first) is not None
                and self._value(reading, self.second) is not None]

    @abstractmethod
    def find(self, readings):
        """The reading at fault, the value to clear and the reason. Or None."""

    def _the_odd_one(self, reading, judgeable):
        """Which instrument is unlike its own column, as an Instrument."""
        return max((self.first, self.second),
                   key=lambda instrument: self._how_far_from_usual(reading, instrument, judgeable))

    def _how_far_from_usual(self, reading, instrument, judgeable):
        """How far this reading sits from what its own instrument usually reads, as a share."""
        usual = median(self._value(row, instrument) for row in judgeable)

        return abs(self._value(reading, instrument) - usual) / abs(usual) if usual else 0.0

    def _says(self, reading, instrument):
        """What that instrument read here, with its own name and unit on it."""
        return f"{instrument.who}'s {self._value(reading, instrument):g} {instrument.unit}"

    @staticmethod
    def _value(reading, instrument):
        return getattr(reading, instrument.field_name)
