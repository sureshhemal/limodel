"""Every number the reading checks compare against, in one place.

Change a number here and every check that uses it changes with it. No check holds a number
of its own, and a test can hand a check different ones.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Thresholds:
    """The numbers the checks use."""

    # --- how many readings are needed, and how many may go ---

    # How many readings a series needs before a check will judge it. With two, each looks
    # as odd as the other, so the check says nothing.
    fewest_readings_to_judge: int = 3

    # How much of one series a check may throw away. If it needs more than a third, the
    # file is wrong rather than the readings, so it stops. More than half would be worse
    # than useless: a median follows the bad values once they outnumber the good ones, and
    # the check starts clearing the readings that were right.
    most_of_a_series_removable: float = 0.34

    # --- the tank weights ---

    # How far a weight may sit from its tank's usual weight. Further than a tenth away and
    # the reading is wrong. The three known bad weights are 90% or more away; every good
    # one is within 5%. A share rather than grammes, because the rinse holds some 4 kg and
    # the concentrate some 2.1 kg.
    impossible_weight_share: float = 0.10

    # --- the pH ---

    # How much the pH may move, and over how long. Readings are 5 to 240 minutes apart, so
    # a rate rather than a step: strict on readings close together, forgiving of slow drift.
    most_ph_change: float = 1.5
    most_ph_change_in_minutes: float = 15.0

    # The range a pH reading has to sit in. Outside it the reading is wrong whatever the
    # readings around it say -- these solutions cannot be at pH 0.07.
    plausible_ph: tuple[float, float] = (2.0, 12.0)

    # --- the temperature ---

    # How much the temperature may move, and over how long. The fastest real change in the
    # data is 0.9 C per quarter of an hour, so 2 C is a wide allowance.
    most_temp_change: float = 2.0
    most_temp_change_in_minutes: float = 15.0

    # The range a temperature has to sit in. The water sits at room temperature: every
    # reading in the data is between 19.9 and 23.0 C.
    plausible_temp_c: tuple[float, float] = (5.0, 40.0)

    # --- the conductivity, which climbs or falls all run ---

    # How big a jump has to be before it counts, as a share of what the series usually
    # reads. Below a tenth, an ordinary wobble on a smooth series looks like a jump.
    smallest_jump_share: float = 0.10

    # How much of the jump the next reading has to put back. A real change of level stays
    # changed; a digit written down wrong is undone at once. At 0.7 this finds seven
    # readings, every one a digit too many or too few.
    comes_back_share: float = 0.7

    # --- the supply current, which is held steady all run ---

    # How far the current may sit from its run's usual reading. It is held to within 2.2%
    # in nineteen of twenty-one runs, so a tenth away is far outside what the supply does.
    impossible_current_share: float = 0.10

    # --- the supply against the multimeter ---

    # How far apart the two voltages may be. They agree to about 0.03 V, so a gap this wide
    # means a digit was written down wrong.
    largest_voltage_gap_v: float = 1.0

    # The range the two currents may differ by, as a ratio. The supply reads about a
    # seventh higher throughout, so they are compared by ratio and not by subtraction.
    plausible_current_ratio: tuple[float, float] = (0.62, 1.6)
