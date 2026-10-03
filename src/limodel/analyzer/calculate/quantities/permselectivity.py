"""How far the stack preferred lithium to magnesium, against the feed it was given."""

from limodel.analyzer.calculate.quantities.feed_ratio import FeedRatio
from limodel.analyzer.calculate.quantities.transport_numbers import TransportNumbers


class Permselectivity:
    """The transport ratio t_li/t_mg held against the ratio the feed offered."""

    @staticmethod
    def find_value(run):
        """None when the transport numbers or the feed ratio cannot be worked out."""
        numbers = TransportNumbers.find_numbers(run)
        feed_ratio = FeedRatio.find_li_over_mg_in_the_dilute(run)

        if numbers is None or feed_ratio is None:
            return None

        t_li, t_mg = numbers

        if t_mg == 0 or feed_ratio == 0:
            return None

        # Dividing by the feed ratio pins no preference at 0.5 whatever the feed was, which
        # is what lets runs fed different lithium to magnesium ratios be compared.
        return (t_li / t_mg) / feed_ratio
