"""Step 2: dropping the runs made on a membrane the modelling is not about."""

from limodel import config
from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess.steps.step import Step
from limodel.models import Run


class DropRunsOnAnotherMembrane(Step):
    """Keeps the runs made on the membranes being modelled.

    A membrane is a different material rather than a setting, so a run on one cannot help fit
    a curve for another. Which membranes are wanted is a setting, so asking a wider question
    needs no edit.
    """

    name = "not a membrane being modelled"

    def __init__(self, membranes: str | tuple[str, ...] | None = None):
        # None defers to the setting, and defers it until apply so a test can change it.
        self.membranes = membranes

    def find_membranes(self) -> tuple[str, ...]:
        """The membranes wanted: the ones this was given, or the ones the settings name."""
        wanted = config.MEMBRANES_MODELLED if self.membranes is None else self.membranes

        # One membrane is the usual case, so it may be given on its own rather than in a list.
        return (wanted,) if isinstance(wanted, str) else tuple(wanted)

    def apply(self, runs: list[Run], journal: Journal) -> list[Run]:
        wanted = self.find_membranes()
        kept = [run for run in runs if run.cem in wanted]

        # Spelling is the likely cause, and modelling nothing in silence would hide it.
        if not kept and runs:
            raise ValueError(
                f"no run is left: none of the {len(runs)} runs is on {', '.join(wanted)}; "
                f"is the membrane spelled as the data spells it?"
            )

        return kept
