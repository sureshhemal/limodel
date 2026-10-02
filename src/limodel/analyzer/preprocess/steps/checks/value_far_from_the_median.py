"""A value that is nothing like the rest of its own series."""

import pandas as pd

from limodel.analyzer.preprocess.steps.checks.check import Check


class ValueFarFromTheMedian(Check):
    """Rejects the value furthest from what this series usually reads.

    For readings that hold one level all run: a tank's weight, the current the supply holds.
    A median cannot be dragged by the one bad value in it, and it does not care whether that
    value sits at the start of the run or the end.
    """

    def __init__(self, field_name, label, unit, share, fewest):
        self.field_name = field_name
        self.label = label
        self.unit = unit
        self.share = share          # how far from the median is too far
        self.fewest = fewest        # how many readings are needed before it will judge

    def find_worst_offender(self, readings):
        """The value furthest from the median, if it is further than the share allows."""
        judgeable = self.find_judgeable_readings(readings)
        by_id = {reading.id: reading for reading in judgeable}
        values = pd.Series({reading.id: getattr(reading, self.field_name)
                            for reading in judgeable})

        if len(values) < self.fewest:
            return None

        middle = values.median()
        distances = (values - middle).abs()
        furthest = distances.idxmax()

        if distances[furthest] <= self.share * abs(middle):
            return None

        return by_id[furthest], self.field_name, (
            f"{self.label} {values[furthest]:g} {self.unit} is {distances[furthest]:g} "
            f"{self.unit} away from the usual {middle:g} {self.unit}")
