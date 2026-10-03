"""How much charge the supply pushed through the stack over a run."""


class ChargeThatPassed:
    """The coulombs under the supply current against time, and the same spread over the area.

    No meter totalled the charge: the current was written down every so many minutes, so the
    charge is the area under those readings.
    """

    @staticmethod
    def find_coulombs(run):
        """None when fewer than two minutes of the power log carry a current."""
        currents = ChargeThatPassed.find_currents_by_minute(run)

        if len(currents) < 2:
            return None

        in_order = sorted(currents)
        amp_minutes = 0.0

        for earlier, later in zip(in_order, in_order[1:]):
            average = (currents[earlier] + currents[later]) / 2
            amp_minutes += average * (later - earlier)

        # A coulomb is an amp-second, and the log counts minutes.
        return amp_minutes * 60

    @staticmethod
    def find_mah_per_cm2(run):
        """None when the charge cannot be worked out, or the run has no membrane area."""
        coulombs = ChargeThatPassed.find_coulombs(run)

        if coulombs is None or not run.area_cm2:
            return None

        # Coulombs to amp-hours, then amps to milliamps.
        return coulombs / (3600 * run.area_cm2) * 1000

    @staticmethod
    def find_currents_by_minute(run):
        """Every minute of the power log that carries a current, keyed by minute."""
        return {reading.minute: reading.supply_current_a
                for reading in run.stack_readings
                if reading.supply_current_a is not None}
