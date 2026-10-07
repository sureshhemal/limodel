"""How far apart runs repeated at the same setting came out."""

import math


class ReplicateScatter:
    """The bench's own scatter in one outcome, pooled over every design point that repeats.

    It is the yardstick a fit is judged against, because a model cannot be better than the
    experiment repeats.
    """

    PLACES = 2  # settings are matched this far to decide two runs sat at the same point

    def __init__(self, field_name):
        self.field_name = field_name

    def find_spread(self, results):
        """The pooled standard deviation and its degrees of freedom; None without a repeat."""
        if results is None:
            return None

        total_squares = 0.0
        degrees_of_freedom = 0

        for values in self.find_groups(results).values():
            if len(values) < 2:
                continue

            middle = sum(values) / len(values)
            total_squares += sum((value - middle) ** 2 for value in values)
            degrees_of_freedom += len(values) - 1

        if degrees_of_freedom == 0:
            return None

        return math.sqrt(total_squares / degrees_of_freedom), degrees_of_freedom

    def find_groups(self, results):
        """The outcome values at each membrane and design point, with gappy runs passed over."""
        groups = {}

        for result in results:
            point = self.find_point_of(result)
            value = getattr(result, self.field_name, None)

            if point is None or value is None:
                continue

            groups.setdefault(point, []).append(value)

        return groups

    def find_point_of(self, result):
        """The membrane and both settings rounded, so repeats of one setting land together."""
        membrane = result.cem
        current_density = result.current_density_ma_cm2
        feed_ratio = result.feed_mg_li_ratio

        if membrane is None or current_density is None or feed_ratio is None:
            return None

        return membrane, round(current_density, self.PLACES), round(feed_ratio, self.PLACES)
