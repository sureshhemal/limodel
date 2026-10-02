"""One instrument's column in the power log."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Instrument:
    """Where one instrument's readings are, what to call it, and what it reads in.

    The supply and the multimeter read the same quantity in different units, so a pair
    cannot share one unit, and a reason that does not name the instrument leaves the reader
    guessing.
    """

    field_name: str   # the column it is written down in
    who: str          # how it is named in a sentence, e.g. "the supply"
    unit: str         # what it reads in, e.g. "mA"
