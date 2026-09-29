"""The record of what the analysis left out, kept as the analysis goes along."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Dropped:
    """A run left out, and the step that left it out.

    The reason travels with the code so the terminal can say more than a count. A run that
    disappears without a reason looks like a bug in the program.
    """

    run_code: str
    reason: str


class Journal:
    """Holds what every stage of the analysis set aside, so one reader can see all of it.

    It is made empty and handed to the analyzer, which hands it on down. Each stage writes
    to the same one, so nothing has to pass exclusions back up through its return value:
    a step still answers with runs alone. Nothing here prints; the command reads it when
    the analysis is over and does the talking.
    """

    def __init__(self):
        self._dropped: list[Dropped] = []

    @property
    def dropped(self) -> tuple[Dropped, ...]:
        """Every run left out so far, in the order it was left out."""
        return tuple(self._dropped)

    def drop(self, run_code: str, reason: str):
        """Writes down one run that will not be modelled, and why."""
        self._dropped.append(Dropped(run_code, reason))
