"""The shape every tank inspector shares."""

from abc import ABC

from limodel.analyzer.preprocess.steps.checks.jump_that_comes_back import JumpThatComesBack
from limodel.analyzer.preprocess.steps.checks.value_far_from_the_median import ValueFarFromTheMedian
from limodel.analyzer.preprocess.steps.checks.value_moving_too_fast import ValueMovingTooFast
from limodel.analyzer.preprocess.steps.checks.value_outside_the_range import ValueOutsideTheRange
from limodel.analyzer.preprocess.steps.inspectors.inspector import Inspector


class TankInspector(Inspector, ABC):
    """An inspector of one tank's readings.

    Every tank is judged on its own readings: a conductivity ordinary in one is impossible
    in another. The checks a tank may be given are built here, so a tank's own class is
    nothing but the list of what it is held to.
    """

    tank: str   # which tank's readings this inspector looks at

    def _find_readings(self, run):
        return sorted((reading for reading in run.tank_readings if reading.tank == self.tank),
                      key=lambda reading: reading.minute)

    def _find_a_weight_unlike_the_others(self):
        """A tank holds about one weight all run, so a reading nothing like it is wrong."""
        return ValueFarFromTheMedian("weight_g", "weight", "g",
                                     self.thresholds.impossible_weight_share,
                                     self.thresholds.fewest_readings_to_judge)

    def _find_a_ph_the_solution_cannot_reach(self):
        """These solutions cannot be at pH 0.07, whatever the readings around it say."""
        return ValueOutsideTheRange("ph", "pH", self.thresholds.plausible_ph)

    def _find_a_ph_that_moved_too_fast(self):
        """The pH drifts. It does not jump a whole unit and a half in a quarter of an hour."""
        return ValueMovingTooFast("ph", "pH", self.thresholds.most_ph_change,
                                  self.thresholds.most_ph_change_in_minutes)

    def _find_a_temperature_the_room_cannot_reach(self):
        """The tanks sit at room temperature all run."""
        return ValueOutsideTheRange("temp_c", "temperature", self.thresholds.plausible_temp_c)

    def _find_a_temperature_that_moved_too_fast(self):
        """Room temperature does not move by degrees between two readings."""
        return ValueMovingTooFast("temp_c", "temperature", self.thresholds.most_temp_change,
                                  self.thresholds.most_temp_change_in_minutes)

    def _find_a_conductivity_jump_that_comes_back(self):
        """Conductivity climbs or falls all run, so there is no one level to compare with.
        A digit written down wrong shows up as a jump the next reading undoes."""
        return JumpThatComesBack("conductivity_us_cm", "conductivity",
                                 self.thresholds.smallest_jump_share,
                                 self.thresholds.comes_back_share)
