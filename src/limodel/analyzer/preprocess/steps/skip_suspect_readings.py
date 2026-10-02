"""Step 2: taking out the readings that cannot be right."""

from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess.steps.inspectors.conc_tank_inspector import ConcTankInspector
from limodel.analyzer.preprocess.steps.inspectors.diluate_tank_inspector import DiluateTankInspector
from limodel.analyzer.preprocess.steps.inspectors.power_log_inspector import PowerLogInspector
from limodel.analyzer.preprocess.steps.inspectors.rinse_tank_inspector import RinseTankInspector
from limodel.analyzer.preprocess.steps.step import Step
from limodel.analyzer.thresholds import Thresholds
from limodel.models import Run


class SkipSuspectReadings(Step):
    """Clears a value a check cannot believe, and writes down why.

    No run is dropped. The reading keeps its minute and its other values; only the one
    that failed turns into None.

    One inspector per tank and one for the power log, each holding the checks its own
    readings get. A tank that turns out to need its own rule is given it in its own class,
    and the others do not move.
    """

    name = "suspect reading"

    def __init__(self, thresholds: Thresholds = Thresholds()):
        self.inspectors = (
            ConcTankInspector(thresholds),
            DiluateTankInspector(thresholds),
            RinseTankInspector(thresholds),
            PowerLogInspector(thresholds),
        )

    def apply(self, runs: list[Run], journal: Journal) -> list[Run]:
        """Puts every run past every inspector."""
        for run in runs:
            for inspector in self.inspectors:
                inspector.inspect(run, journal)

        return runs
