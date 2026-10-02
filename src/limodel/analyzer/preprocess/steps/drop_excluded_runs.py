"""Step 1: dropping the runs that are not marked for use."""

from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess.steps.step import Step
from limodel.models import Run


class DropExcludedRuns(Step):
    """Keeps the runs marked for use.

    The mark is a decision taken at the bench, so this only obeys it. If no run is left it
    stops: that means the wrong file.
    """

    name = "not marked for use"

    def apply(self, runs: list[Run], journal: Journal) -> list[Run]:
        marked_for_use = [run for run in runs if run.include]

        if not marked_for_use and runs:
            raise ValueError(
                f"no run is left: all {len(runs)} are marked not to be used; is this the right data?"
            )

        return marked_for_use
