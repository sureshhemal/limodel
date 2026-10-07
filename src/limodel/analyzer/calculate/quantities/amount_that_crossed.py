"""How much of a metal moved into a tank over the run."""

from limodel.analyzer.calculate.constants import TARE_FIELD_BY_TANK
from limodel.analyzer.calculate.quantities.amount_in_a_tank import AmountInATank


class AmountThatCrossed:
    """The milligrams of a metal a tank ended with, less the milligrams it started with.

    Only the sampled minutes count, and the readings arrive in no particular order, so the
    ends are found by minute rather than by position.
    """

    @staticmethod
    def find_milligrams(run, tank, metal):
        """None when the run has no two sampled minutes to span."""
        ends = AmountThatCrossed.find_ends(run, tank, metal)

        if ends is None:
            return None

        start_mg, end_mg = ends

        return end_mg - start_mg

    @staticmethod
    def find_ends(run, tank, metal):
        """(start_mg, end_mg) for the tank, which recovery and the feed ratio need apart."""
        if tank not in TARE_FIELD_BY_TANK:
            return None

        tare_g = getattr(run, TARE_FIELD_BY_TANK[tank], None)
        amounts = AmountThatCrossed.find_amounts_by_minute(run, tank, metal, tare_g)

        if len(amounts) < 2:
            return None

        in_order = sorted(amounts)

        return amounts[in_order[0]], amounts[in_order[-1]]

    @staticmethod
    def find_amounts_by_minute(run, tank, metal, tare_g):
        """Every minute of this tank that can be turned into milligrams, keyed by minute."""
        amounts = {}

        for reading in run.tank_readings:
            if reading.tank != tank:
                continue

            milligrams = AmountInATank.find_milligrams(reading, tare_g, metal)

            if milligrams is not None:
                amounts[reading.minute] = milligrams

        return amounts
