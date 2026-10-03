"""One row of a file the schema would not take."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RejectedRow:
    """A row left out at the door, named so a reader can go and fix it.

    It carries the kind of record it would have become, because the journal reports a run
    differently from a reading and a rejected row never becomes either.
    """

    id: str
    model: str
    reason: str
