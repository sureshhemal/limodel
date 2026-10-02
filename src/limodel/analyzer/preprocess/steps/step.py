"""The shape every preprocessing step shares."""

from abc import ABC, abstractmethod

from limodel.analyzer.journal import Journal
from limodel.models import Run


class Step(ABC):
    """One preprocessing step: runs in, the runs that survive it out.

    A step that filters returns a shorter list and leaves the runs themselves alone. A step
    that cleans returns every run it was given, with values it cannot believe set to None.
    Either way it writes what it left out to the journal and prints nothing: the command
    reads the journal when the analysis is over and does the talking.
    """

    name: str  # a short label for the report, e.g. "not marked for use"

    @abstractmethod
    def apply(self, runs: list[Run], journal: Journal) -> list[Run]:
        """The runs after this step."""
