"""The modelling, start to finish."""

from dataclasses import dataclass

from limodel.analyzer.calculate.calculator import Calculator
from limodel.analyzer.calculate.result import Result
from limodel.analyzer.journal import Journal
from limodel.analyzer.model.surrogate import Surrogate
from limodel.analyzer.model.surrogate_models import SurrogateModels
from limodel.analyzer.preprocess import Preprocessor
from limodel.models import Run


@dataclass(frozen=True)
class Analysis:
    """What the modelling worked from, and what it made of it.

    The runs left out are part of the finding, not a footnote: a polynomial from sixteen
    runs and one from twenty-one are different claims. The results travel beside the runs
    rather than replacing them, because a reader checking a number wants the readings it
    came from.
    """

    used: list[Run]
    results: list[Result]
    models: SurrogateModels


class Analyzer:
    """Drives the modelling, from loaded runs to the best setup.

    Each stage lives in its own module and this class is the order they run in. The journal
    it is given is empty at the start and filled as it goes.
    """

    def __init__(self, loader, journal: Journal):
        self.loader = loader
        self.journal = journal

    def analyze(self) -> Analysis:
        loaded = self.loader.load()
        self._record_what_would_not_load()
        runs = Preprocessor(self.journal).run(loaded)
        results = Calculator(self.journal).find_results(runs)

        return Analysis(
            used=runs,
            results=results,
            models=Surrogate(self.journal).find_models(results)
        )

    def _record_what_would_not_load(self):
        """Writes down every row the schema would not take, so a reader learns of it.

        A row the files cannot be read without used to stop the whole run. It is a finding
        like any other now: named, with the reason, while the rest of the work goes on.
        """
        for row in self.loader.find_refused_rows():
            self.journal.drop(row, row.reason)


# The stages still to build, in the order they run.
#
# 1. Look before trusting. Plot permselectivity and recovery against current density,
#    one line per membrane, with the replicate scatter as error bars. The shape says
#    whether the curvature the fitting kept is real.
#
# 2. Name the next runs. The gaps the search cannot fill are the experiments worth
#    doing, and saying which ones they are is part of the finding.
