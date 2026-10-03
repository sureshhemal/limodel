"""How much lithium the feed offers per magnesium, measured in the tank and as set up."""

from limodel.analyzer.calculate.constants import DILUTE, TARE_FIELD_BY_TANK
from limodel.analyzer.calculate.metal import LITHIUM, MAGNESIUM
from limodel.analyzer.calculate.quantities.amount_that_crossed import AmountThatCrossed


class FeedRatio:
    """The feed's lithium to magnesium ratio in millimoles per litre, two ways.

    The two are kept apart by name because they answer different questions: the measured
    one is what permselectivity divides by, the set up one is a design column of the model.
    """

    @staticmethod
    def find_li_over_mg_in_the_dilute(run):
        """Li over Mg at the first dilute minute the lab reported both metals for."""
        tare_g = getattr(run, TARE_FIELD_BY_TANK[DILUTE], None)
        li_by_minute = AmountThatCrossed.find_amounts_by_minute(run, DILUTE, LITHIUM, tare_g)
        mg_by_minute = AmountThatCrossed.find_amounts_by_minute(run, DILUTE, MAGNESIUM,
                                                                tare_g)
        both_reported = sorted(set(li_by_minute) & set(mg_by_minute))

        if not both_reported:
            return None

        first = both_reported[0]

        # One tank at one minute, so the litres cancel and the milligrams carry the ratio.
        mg_mmol = mg_by_minute[first] / MAGNESIUM.g_per_mol

        if mg_mmol == 0:
            return None

        return (li_by_minute[first] / LITHIUM.g_per_mol) / mg_mmol

    @staticmethod
    def find_mg_over_li_from_the_setup(run):
        """Mg over Li from the run's own feed concentrations, the other way up."""
        if run.li_feed_mg_l is None or run.mg_feed_mg_l is None:
            return None

        li_mmol = run.li_feed_mg_l / LITHIUM.g_per_mol

        if li_mmol == 0:
            return None

        return (run.mg_feed_mg_l / MAGNESIUM.g_per_mol) / li_mmol
