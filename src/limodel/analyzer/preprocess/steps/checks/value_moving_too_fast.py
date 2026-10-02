"""A value that moved further than it had time for."""

from itertools import pairwise
from statistics import median

from limodel.analyzer.preprocess.steps.checks.check import Check


class ValueMovingTooFast(Check):
    """Rejects the reading behind the fastest change, when it is faster than allowed.

    Readings are 5 to 240 minutes apart, so the allowance is a rate rather than a step:
    strict on readings close together, forgiving of slow drift over hours. Two readings
    that move too far too quickly cannot both be right, and the one further from the usual
    level is taken to be the wrong one.
    """

    def __init__(self, field_name, label, allowance, over_minutes):
        self.field_name = field_name
        self.label = label
        self.allowance = allowance          # how much it may move
        self.over_minutes = over_minutes    # in how long

    def find(self, readings):
        """The reading behind the fastest change over the allowance."""
        judgeable = self.judgeable(readings)
        if len(judgeable) < 2:
            return None

        allowed_per_minute = self.allowance / self.over_minutes
        middle = median(self._value(reading) for reading in judgeable)

        worst = None
        for before, after in pairwise(judgeable):
            minutes = after.minute - before.minute
            change = abs(self._value(after) - self._value(before))
            if minutes <= 0 or change / minutes <= allowed_per_minute:
                continue

            if worst is None or change / minutes > worst[0]:
                worst = (change / minutes, self._the_odd_one(before, after, middle), minutes, change)

        if worst is None:
            return None

        _, reading, minutes, change = worst

        return reading, self.field_name, (
            f"{self.label} moved {change:g} in {minutes} minutes, more than "
            f"{self.allowance:g} in {self.over_minutes:g}")

    def _the_odd_one(self, before, after, middle):
        """Of two readings that cannot both be right, the one unlike the rest."""
        return max((before, after), key=lambda reading: abs(self._value(reading) - middle))

    def _value(self, reading):
        return getattr(reading, self.field_name)
