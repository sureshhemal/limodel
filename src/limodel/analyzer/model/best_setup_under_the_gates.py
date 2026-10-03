"""The most selective setup that still clears the recovery floor and the voltage ceiling."""

import itertools

from limodel import config
from limodel.analyzer.model.design_points import DesignPoints

PERMSELECTIVITY = "permselectivity"
LI_RECOVERY = "li_recovery_pct"
HIGHEST_VOLTAGE = "highest_voltage_v"

# The three outcomes the search needs: the one it maximises, and the two with gates on them.
OUTCOME_NAMES = (PERMSELECTIVITY, LI_RECOVERY, HIGHEST_VOLTAGE)


class BestSetupUnderTheGates:
    """The setup with the highest predicted permselectivity that both gates let through.

    It sweeps only inside the measured range on purpose: the answer has to be a setup the
    bench has evidence for, not a reading taken past the last run. Nothing surviving is a
    finding and not an error, so the gate that turned every point away is reported too.
    """

    STEPS = 21                  # levels per setting, a tenth of the coded span apart

    RECOVERY_GATE = "lithium recovery floor"
    VOLTAGE_GATE = "voltage ceiling"

    def __init__(self, design_points, permselectivity, li_recovery, highest_voltage,
                 recovery_floor_pct=None, voltage_ceiling_v=None, steps=STEPS):
        self.design_points = design_points
        self.permselectivity = permselectivity
        self.li_recovery = li_recovery
        self.highest_voltage = highest_voltage
        # None defers to the settings, so a floor can be changed without touching the code.
        self.recovery_floor_pct = (config.RECOVERY_FLOOR_PCT if recovery_floor_pct is None
                                   else recovery_floor_pct)
        self.voltage_ceiling_v = (config.VOLTAGE_CEILING_V if voltage_ceiling_v is None
                                  else voltage_ceiling_v)
        self.steps = steps

    def find_settings(self):
        """The winning setup in mA/cm2 and mol/mol; None when there is no answer to give."""
        return self.design_points.find_real_from_coded(self.find_best_point())

    def find_best_point(self):
        """The surviving coded point with the most permselectivity; None when none survived."""
        survivors = self.find_survivors()

        if not survivors:
            return None

        return max(survivors,
                   key=lambda point: self.find_predictions_at(point)[PERMSELECTIVITY])

    def find_best_predictions(self):
        """All three outcomes where the winner sits, which is what the report quotes."""
        return self.find_predictions_at(self.find_best_point())

    def find_best_point_without_the_gates(self):
        """The most selective point swept, gates set aside; None when none can be predicted.

        A refusal on its own leaves a reader nowhere. The best the runs can offer is still
        worth seeing, as long as it is shown with what it falls short on.
        """
        predictable = [point for point in self.find_coded_grid()
                       if self.find_predictions_at(point) is not None]

        if not predictable:
            return None

        return max(predictable,
                   key=lambda point: self.find_predictions_at(point)[PERMSELECTIVITY])

    def find_settings_without_the_gates(self):
        """That same point in mA/cm2 and mol/mol; None when it cannot be put in real units."""
        return self.design_points.find_real_from_coded(self.find_best_point_without_the_gates())

    def find_predictions_without_the_gates(self):
        """All three outcomes at that point, so the report can say what it would give."""
        return self.find_predictions_at(self.find_best_point_without_the_gates())

    def find_shortfalls(self, coded_row):
        """How far one point misses each gate it fails, as {gate: how far}; empty when it passes."""
        predictions = self.find_predictions_at(coded_row)

        if predictions is None:
            return {}

        missed = {}

        if predictions[LI_RECOVERY] < self.recovery_floor_pct:
            missed[self.RECOVERY_GATE] = self.recovery_floor_pct - predictions[LI_RECOVERY]

        if predictions[HIGHEST_VOLTAGE] > self.voltage_ceiling_v:
            missed[self.VOLTAGE_GATE] = predictions[HIGHEST_VOLTAGE] - self.voltage_ceiling_v

        return missed

    def find_refusal(self):
        """Why there is no answer, naming the gate that did it; None when there is one."""
        if self.find_settings() is not None:
            return None

        if self.find_best_point() is not None:
            return "the runs do not cover enough ground to place a setup in real units"

        blamed = [gate for gate, count in self.find_rejections().items() if count]

        if not blamed:
            return "no setup inside the measured range could be predicted"

        return f"nothing inside the measured range cleared the {' and the '.join(blamed)}"

    def find_rejections(self):
        """How many of the swept points each gate turned away."""
        counts = {self.RECOVERY_GATE: 0, self.VOLTAGE_GATE: 0}

        for point in self.find_coded_grid():
            for gate in self.find_gates_failed_at(point) or ():
                counts[gate] += 1

        return counts

    def find_survivors(self):
        """Every swept point that clears both gates."""
        return [point for point in self.find_coded_grid()
                if self.find_gates_failed_at(point) == []]

    def find_gates_failed_at(self, coded_row):
        """The gates one point falls foul of; None when it cannot be predicted at all."""
        predictions = self.find_predictions_at(coded_row)

        if predictions is None:
            return None

        failed = []

        if predictions[LI_RECOVERY] < self.recovery_floor_pct:
            failed.append(self.RECOVERY_GATE)

        if predictions[HIGHEST_VOLTAGE] > self.voltage_ceiling_v:
            failed.append(self.VOLTAGE_GATE)

        return failed

    def find_predictions_at(self, coded_row):
        """All three outcomes at one coded point; None when any one of them cannot be had."""
        found = {PERMSELECTIVITY: self.permselectivity.find_prediction(coded_row),
                 LI_RECOVERY: self.li_recovery.find_prediction(coded_row),
                 HIGHEST_VOLTAGE: self.highest_voltage.find_prediction(coded_row)}

        if any(value is None for value in found.values()):
            return None

        return found

    def find_coded_grid(self):
        """Every point swept, in coded units, one axis per setting."""
        return list(itertools.product(self.find_levels(),
                                      repeat=len(DesignPoints.SETTING_NAMES)))

    def find_levels(self):
        """The coded levels swept in each setting, from the lowest run to the highest."""
        if self.steps < 2:
            return []

        # Coded units run -1..1 across the fitted runs by construction, so sweeping that span
        # and no further is what keeps the answer inside the ground the bench covered.
        return [-1.0 + 2.0 * step / (self.steps - 1) for step in range(self.steps)]
