"""The concentrate tank: what it is held to."""

from limodel.analyzer.preprocess.steps.inspectors.tank_inspector import TankInspector


class ConcTankInspector(TankInspector):
    """The concentrate, which gains weight and conductivity as the ions arrive."""

    tank = "conc"

    def _checks(self):
        return (
            self._a_weight_unlike_the_others(),
            self._a_ph_the_solution_cannot_reach(),
            self._a_ph_that_moved_too_fast(),
            self._a_temperature_the_room_cannot_reach(),
            self._a_temperature_that_moved_too_fast(),
            self._a_conductivity_jump_that_comes_back(),
        )
