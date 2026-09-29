"""The shape every preprocessing step shares."""

from abc import ABC, abstractmethod

from limodel.models import Run


class Step(ABC):
    """One preprocessing step: runs in, the runs that survive it out.

    The list it is given is never changed, and a step never prints: the preprocessor keeps
    the record of what each one removed, and the command does the talking.
    """

    name: str  # a short label for the report, e.g. "not marked for use"

    @abstractmethod
    def apply(self, runs: list[Run]) -> list[Run]:
        """The runs after this step."""
