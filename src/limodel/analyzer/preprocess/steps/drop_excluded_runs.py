"""Step 1: dropping the runs that are not marked for use."""

from limodel.analyzer.preprocess.steps.step import Step
from limodel.models import Run


class DropExcludedRuns(Step):
    """Drops every run whose mark says not to use it.

    Whether a run counts is decided at the bench and recorded with the run, so this step
    only obeys that mark. If no run is left, the run stops: that means the wrong file, not
    a few set-aside experiments.
    """

    name = "not marked for use"

    def apply(self, runs: list[Run]) -> list[Run]:
        marked_for_use = [run for run in runs if run.include]

        if not marked_for_use and runs:
            raise ValueError(
                f"no run is left: all {len(runs)} are marked not to be used; is this the right data?"
            )

        return marked_for_use
