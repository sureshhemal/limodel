"""What the electricity cost for every mole of lithium a run moved."""

from limodel.analyzer.calculate.constants import CONCENTRATE
from limodel.analyzer.calculate.metal import LITHIUM
from limodel.analyzer.calculate.quantities.amount_that_crossed import AmountThatCrossed


class EnergyPerMoleOfLithium:
    """The watt-hours under the supply power curve, per mole of lithium reaching the concentrate.

    Per mole of lithium rather than per hour or per litre, so a short run and a long one, or
    a gentle current and a hard one, can be set beside each other.
    """

    @staticmethod
    def find_watt_hours(run):
        """None when the power log is too short, or no lithium crossed to spend it on."""
        joules = EnergyPerMoleOfLithium.find_joules(run)
        crossed_mg = AmountThatCrossed.find_milligrams(run, CONCENTRATE, LITHIUM)

        if joules is None or crossed_mg is None:
            return None

        moles = crossed_mg / 1000 / LITHIUM.g_per_mol

        # A concentrate that gained no lithium, or lost some, has no per-mole cost to report.
        if moles <= 0:
            return None

        return joules / 3600 / moles

    @staticmethod
    def find_joules(run):
        """None when fewer than two minutes of the log carry both a voltage and a current."""
        watts = EnergyPerMoleOfLithium.find_watts_by_minute(run)

        if len(watts) < 2:
            return None

        in_order = sorted(watts)
        watt_minutes = 0.0

        for earlier, later in zip(in_order, in_order[1:]):
            average = (watts[earlier] + watts[later]) / 2
            watt_minutes += average * (later - earlier)

        # A joule is a watt-second, and the log counts minutes.
        return watt_minutes * 60

    @staticmethod
    def find_watts_by_minute(run):
        """Every minute of the power log that gives a power, keyed by minute."""
        return {reading.minute: reading.supply_voltage_v * reading.supply_current_a
                for reading in run.stack_readings
                if reading.supply_voltage_v is not None
                and reading.supply_current_a is not None}
