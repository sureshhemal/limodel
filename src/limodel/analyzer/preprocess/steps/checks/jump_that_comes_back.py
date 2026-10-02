"""A reading that jumps away from its series and is immediately undone."""

from statistics import median

from limodel.analyzer.preprocess.steps.checks.check import Check


class JumpThatComesBack(Check):
    """Rejects a reading that jumps and whose next reading jumps straight back.

    For readings that climb or fall all run, where there is no one level to compare against.
    A real change of level stays changed; a digit written down wrong is undone at once.
    """

    def __init__(self, field_name, label, smallest_jump_share, comes_back_share):
        self.field_name = field_name
        self.label = label
        self.smallest_jump_share = smallest_jump_share   # how big a jump has to be to count
        self.comes_back_share = comes_back_share         # how much of it has to come back

    def find_worst_offender(self, readings):
        """The reading in the middle of the first jump-and-back."""
        judgeable = self.find_judgeable_readings(readings)
        if len(judgeable) < 3:
            return None

        values = [getattr(reading, self.field_name) for reading in judgeable]
        middle = median(values)

        for at in range(len(values) - 2):
            jump = values[at + 1] - values[at]
            back = values[at + 2] - values[at + 1]
            if not jump or abs(jump) <= self.smallest_jump_share * abs(middle):
                continue

            came_back = -back / jump
            if came_back < self.comes_back_share:
                continue

            return judgeable[at + 1], self.field_name, (
                f"{self.label} jumped to {values[at + 1]:g} and the next reading put "
                f"{came_back:.0%} of it back")

        return None
