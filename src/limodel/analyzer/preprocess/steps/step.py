"""The shape every preprocessing step shares."""

from abc import ABC, abstractmethod

from limodel.analyzer.journal import Journal
from limodel.models import Run


class Step(ABC):
    """One preprocessing step: runs in, the runs that survive it out.

    A filtering step returns fewer runs. A cleaning step returns them all with values it
    cannot believe set to None. Either way it prints nothing.
    """

    name: str  # a short label for the report, e.g. "not marked for use"

    @abstractmethod
    def apply(self, runs: list[Run], journal: Journal) -> list[Run]:
        """The runs after this step."""
