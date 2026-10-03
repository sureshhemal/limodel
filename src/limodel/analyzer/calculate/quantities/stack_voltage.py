"""What the supply had to push to hold the current through the stack."""


class StackVoltage:
    """The highest volts a run reached, and the volts it began at.

    The highest says whether the run stayed under the supply's ceiling; the start says how
    much the stack asked for before anything had moved across the membranes.
    """

    @staticmethod
    def find_highest_volts(run):
        """None when the power log never recorded a voltage."""
        volts = StackVoltage.find_volts_by_minute(run)

        if not volts:
            return None

        return max(volts.values())

    @staticmethod
    def find_starting_volts(run):
        """The voltage at the earliest minute that has one, which need not be the lowest."""
        volts = StackVoltage.find_volts_by_minute(run)

        if not volts:
            return None

        return volts[min(volts)]

    @staticmethod
    def find_volts_by_minute(run):
        """Every minute of the power log that carries a voltage, keyed by minute."""
        return {reading.minute: reading.supply_voltage_v
                for reading in run.stack_readings
                if reading.supply_voltage_v is not None}
