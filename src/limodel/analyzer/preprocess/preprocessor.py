"""The loaded runs → the runs the modelling uses."""

from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess.steps.drop_excluded_runs import DropExcludedRuns
from limodel.analyzer.preprocess.steps.step import Step
from limodel.models import Run


class Preprocessor:
    """Runs each preprocessing step in order, each one on the runs the one before it returned.

    Nothing is saved: the result is returned. The list it is given is never changed. Whatever
    a step removes is written to the journal under that step's name, so the steps themselves
    stay simple: runs in, runs out.
    """

    steps: tuple[Step, ...] = (
        DropExcludedRuns(),
    )

    def __init__(self, journal: Journal):
        self.journal = journal

    def run(self, runs: list[Run]) -> list[Run]:
        selected = runs
        for step in self.steps:
            after = step.apply(selected)
            self._write_down_what_went(step, selected, after)
            selected = after

        return selected

    def _write_down_what_went(self, step, before, after):
        """Notes every run this step took out, under the step's own name."""
        left = {run.run_code for run in after}

        for run in before:
            if run.run_code not in left:
                self.journal.drop(run.run_code, step.name)
