"""The rinse tank: what it is held to."""

from limodel.analyzer.preprocess.steps.inspectors.tank_inspector import TankInspector


class RinseTankInspector(TankInspector):
    """The rinse, which the chemistry does not use. A reading it cannot have is still a
    reading written down wrong, so it is held to the same rules."""

    tank = "rinse"

    def _find_checks(self):
        return (
            self._find_a_weight_unlike_the_others(),
            self._find_a_ph_the_solution_cannot_reach(),
            self._find_a_ph_that_moved_too_fast(),
            self._find_a_temperature_the_room_cannot_reach(),
            self._find_a_temperature_that_moved_too_fast(),
            self._find_a_conductivity_jump_that_comes_back(),
        )
