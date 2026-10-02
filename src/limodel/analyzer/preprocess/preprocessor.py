"""The loaded runs → the runs the modelling uses."""

from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess.steps.drop_excluded_runs import DropExcludedRuns
from limodel.analyzer.preprocess.steps.drop_runs_missing_an_end_sample import DropRunsMissingAnEndSample
from limodel.analyzer.preprocess.steps.skip_suspect_readings import SkipSuspectReadings
from limodel.analyzer.preprocess.steps.step import Step
from limodel.models import Run


class Preprocessor:
    """Runs each step in order, each on the runs the one before it returned.

    Nothing is saved: the result is returned. Whatever a step removes is written to the
    journal under that step's name.
    """

    steps: tuple[Step, ...] = (
        DropExcludedRuns(),
        # if run is missing required field, that is already dropped by data loader from csv.
        # So, we'll not handle that issue in here anymore.
        SkipSuspectReadings(),
        DropRunsMissingAnEndSample(),
    )

    def __init__(self, journal: Journal):
        self.journal = journal

    def run(self, runs: list[Run]) -> list[Run]:
        selected_runs = runs
        for step in self.steps:
            filtered_runs = step.apply(selected_runs, self.journal)
            self._record_ignored_runs(step.name, selected_runs, filtered_runs)
            selected_runs = filtered_runs

        return selected_runs

    def _record_ignored_runs(self, step_name: str, before, after):
        """Notes every run this step took out, under the step's own name."""
        left = {run.run_code for run in after}

        for run in before:
            if run.run_code not in left:
                self.journal.drop(run, step_name)
