"""How much of a metal the readings never account for."""

from limodel.analyzer.calculate.constants import CONCENTRATE, DILUTE, RINSE
from limodel.analyzer.calculate.quantities.amount_that_crossed import AmountThatCrossed


class BalanceGap:
    """The percent of what the dilute lost that was not found in the other two tanks.

    A diagnostic only, and mostly the liquid left behind in the sample bottles. Nothing is
    ever corrected by it.
    """

    @staticmethod
    def find_percent(run, metal):
        """None when the loss or the concentrate's gain is unworkable, or nothing was lost."""
        feed_ends = AmountThatCrossed.find_ends(run, DILUTE, metal)
        gained_mg = AmountThatCrossed.find_milligrams(run, CONCENTRATE, metal)

        if feed_ends is None or gained_mg is None:
            return None

        lost_mg = feed_ends[0] - feed_ends[1]

        # A share of a loss means nothing where there was no loss, and a dilute that gained
        # would turn the sign of the gap over, so neither has a gap to report.
        if lost_mg <= 0:
            return None

        rinse_mg = AmountThatCrossed.find_milligrams(run, RINSE, metal)

        # The rinse was often never weighed. Counting it as nothing gained can only make the
        # gap look worse, which is the honest way for a diagnostic to be wrong.
        if rinse_mg is None:
            rinse_mg = 0.0

        return 100 * (lost_mg - (gained_mg + rinse_mg)) / lost_mg
