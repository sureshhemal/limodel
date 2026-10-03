"""The share of the charge each metal carried into the concentrate."""

from limodel.analyzer.calculate.constants import CONCENTRATE
from limodel.analyzer.calculate.metal import LITHIUM, MAGNESIUM
from limodel.analyzer.calculate.quantities.amount_that_crossed import AmountThatCrossed


class TransportNumbers:
    """The fraction of the charge carried by lithium and by magnesium, as (t_li, t_mg).

    A transport number is a share of the charge and not of the ions, so each metal is
    counted in millimoles and weighted by the charge its own ion carries.
    """

    @staticmethod
    def find_numbers(run):
        """None when either metal's crossing is unknown, or no charge crossed at all."""
        li_mg = AmountThatCrossed.find_milligrams(run, CONCENTRATE, LITHIUM)
        mg_mg = AmountThatCrossed.find_milligrams(run, CONCENTRATE, MAGNESIUM)

        if li_mg is None or mg_mg is None:
            return None

        li_carried = LITHIUM.charge * li_mg / LITHIUM.g_per_mol
        mg_carried = MAGNESIUM.charge * mg_mg / MAGNESIUM.g_per_mol
        carried = li_carried + mg_carried

        if carried == 0:
            return None

        return li_carried / carried, mg_carried / carried
