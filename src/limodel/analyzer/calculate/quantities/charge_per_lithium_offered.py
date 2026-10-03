"""How much charge was pushed for each lithium the feed offered."""

from limodel.analyzer.calculate.constants import DILUTE, FARADAY_C_PER_MOL
from limodel.analyzer.calculate.metal import LITHIUM
from limodel.analyzer.calculate.quantities.amount_that_crossed import AmountThatCrossed
from limodel.analyzer.calculate.quantities.charge_that_passed import ChargeThatPassed

SECONDS_PER_HOUR = 3600.0
MMOL_PER_MOL = 1000.0


class ChargePerLithiumOffered:
    """Moles of charge pushed through, per mole of lithium the dilute started with.

    Recovery is what moved over what was there, and what moved follows the charge, so this
    is the one number saying how hard a run was pushed. It takes in the run's length, the
    size of the tank and the strength of the feed at once: the same charge into a tank twice
    the size is a gentler run, which mA.h/cm2 cannot say and this can.

    1.0 means just enough charge was pushed to move every lithium on offer, had lithium
    carried all of it. Anything above 1 is the cost of magnesium competing for the current.
    """

    @staticmethod
    def find_equivalents(run):
        """None when the charge or the lithium the feed offered cannot be worked out."""
        coulombs = ChargeThatPassed.find_coulombs(run)
        ends = AmountThatCrossed.find_ends(run, DILUTE, LITHIUM)

        if coulombs is None or ends is None or not run.cell_pairs:
            return None

        offered_mol = ends[0] / LITHIUM.g_per_mol / MMOL_PER_MOL

        if offered_mol == 0:
            return None

        return coulombs * run.cell_pairs / FARADAY_C_PER_MOL / offered_mol

    @staticmethod
    def find_hours(equivalents, offered_mmol, cell_pairs, current_a):
        """How long to run for, to reach that many equivalents at a current held steady.

        The inverse of find_equivalents, and the answer to "so how long do I run it":

            t = (charge per Li) x (mmol Li available) x F / (cell pairs x current)

        with the millimoles turned into moles and the seconds into hours. F is Faraday's
        constant, 96485 coulombs per mole of charge.
        """
        if not current_a or not cell_pairs or equivalents is None or offered_mmol is None:
            return None

        seconds = (equivalents * (offered_mmol / MMOL_PER_MOL) * FARADAY_C_PER_MOL
                   / (cell_pairs * current_a))

        return seconds / SECONDS_PER_HOUR
