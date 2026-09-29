"""Every number the reading checks compare against, in one place.

Each one is written next to the evidence it came from, so changing it is a decision made
with the data in view rather than a guess. A step is handed these rather than holding its
own numbers, so a test can pass different ones and nothing has to be edited in two places.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Thresholds:
    """What counts as impossible, and what counts as worth a second look."""

    # --- weights: five readings per series, so the rules are physical, not statistical ---

    # A step larger than this share of the tank's own median weight cannot happen: no one
    # adds or removes a tenth of a tank between two readings. At 0.10 this flags exactly
    # three readings in 340 steps, all three known breaks; at 0.05 it also picks up AL's
    # diluate, which is odd but not impossible.
    impossible_weight_step_share: float = 0.10

    # Below this, a flagged weight step is not worth reporting: 7 of 51 series have a MAD
    # under 1 g, which makes a 10 g wobble score as an outlier.
    suspect_weight_step_g: float = 20.0

    # --- the statistic used on the columns that have enough readings ---

    # Modified z-score, (0.6745 x (value - median)) / MAD. 3.5 is the usual cutoff.
    modified_z: float = 3.5

    # A single bad reading shows up as a jump followed by a jump back. The reversal has to
    # undo at least this share of the jump to count as one. Without it, MAD alone flags 98
    # of 957 conductivity differences.
    reversal_share: float = 0.7

    # --- columns with their own physical scale ---

    # Consecutive pH readings move by hundredths. A whole unit is a typo: AT's concentrate
    # reads 0.072 between 5.083 and 5.06.
    suspect_ph_step: float = 1.0

    # Temperature is held to a tenth of a degree, so its MAD is exactly zero in 46 of 58
    # series and no statistic can be built from it. A tolerance stands in.
    suspect_temp_step_c: float = 2.0
    plausible_temp_c: tuple[float, float] = (5.0, 40.0)

    # --- the two instruments, held against each other ---

    # Supply and multimeter voltage agree to a median of 0.03 V across 889 paired rows.
    # A gap this size means one of them was written down wrong: 9 rows, every one a
    # dropped or added leading digit.
    suspect_voltage_gap_v: float = 1.0

    # The supply reads about 14% higher than the multimeter throughout (median ratio 1.14,
    # 5th to 95th 1.07-1.49), so the currents are compared as a ratio, not a difference.
    # This band flags 5 rows, including a supply current recorded as 0.46 A for 36.8 mA.
    plausible_current_ratio: tuple[float, float] = (0.62, 1.6)
