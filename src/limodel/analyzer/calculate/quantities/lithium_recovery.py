"""How much of the feed lithium ended up in the concentrate."""

from limodel.analyzer.calculate.constants import CONCENTRATE, DILUTE
from limodel.analyzer.calculate.metal import LITHIUM
from limodel.analyzer.calculate.quantities.amount_that_crossed import AmountThatCrossed


class LithiumRecovery:
    """The percent of the lithium the feed started with that crossed into the concentrate.

    Milligrams stand on both sides of the division, so the molar mass cancels and there is
    nothing to gain by going through moles.
    """

    @staticmethod
    def find_percent(run):
        """None when either end is missing, or the feed started with no lithium."""
        crossed_mg = AmountThatCrossed.find_milligrams(run, CONCENTRATE, LITHIUM)
        feed_ends = AmountThatCrossed.find_ends(run, DILUTE, LITHIUM)

        if crossed_mg is None or feed_ends is None:
            return None

        # What the feed held before anything moved is the whole prize, so recovery is
        # measured against its first sampled minute, never against what it ended with.
        feed_mg = feed_ends[0]

        if feed_mg == 0:
            return None

        return 100 * crossed_mg / feed_mg
