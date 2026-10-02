"""A value that moved further than it had time for."""

from itertools import pairwise
from statistics import median

from limodel.analyzer.preprocess.steps.checks.check import Check


class ValueMovingTooFast(Check):
    """Rejects the reading behind the fastest change, when it is faster than allowed.

    Readings are 5 to 240 minutes apart, so the allowance is a rate, not a step. Of two
    readings that cannot both be right, the one further from the usual level is blamed.
    """

    def __init__(self, field_name, label, allowance, over_minutes):
        self.field_name = field_name
        self.label = label
        self.allowance = allowance          # how much it may move
        self.over_minutes = over_minutes    # in how long

    def find_worst_offender(self, readings):
        """The reading behind the fastest change over the allowance."""
        judgeable = self.find_judgeable_readings(readings)
        if len(judgeable) < 2:
            return None

        allowed_per_minute = self.allowance / self.over_minutes
        middle = median(self._find_value(reading) for reading in judgeable)

        worst = None
        for before, after in pairwise(judgeable):
            minutes = after.minute - before.minute
            change = abs(self._find_value(after) - self._find_value(before))
            if minutes <= 0 or change / minutes <= allowed_per_minute:
                continue

            if worst is None or change / minutes > worst[0]:
                worst = (change / minutes, self._find_odd_one(before, after, middle), minutes, change)

        if worst is None:
            return None

        _, reading, minutes, change = worst

        return reading, self.field_name, (
            f"{self.label} moved {change:g} in {minutes} minutes, more than "
            f"{self.allowance:g} in {self.over_minutes:g}")

    def _find_odd_one(self, before, after, middle):
        """Of two readings that cannot both be right, the one unlike the rest."""
        return max((before, after), key=lambda reading: abs(self._find_value(reading) - middle))

    def _find_value(self, reading):
        return getattr(reading, self.field_name)
