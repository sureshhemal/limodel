"""The modelling, start to finish."""

from dataclasses import dataclass

from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess import Preprocessor
from limodel.models import Run


@dataclass(frozen=True)
class Analysis:
    """What the modelling worked from, and what it found.

    The runs left out are part of the finding, not a footnote: a polynomial fitted from
    sixteen runs and one fitted from twenty-one are different claims.
    """

    used: list[Run]
    waiting: list[str]


class Analyzer:
    """Drives the modelling, from loaded runs to the best setup.

    Each stage of the modelling lives in its own module in this package, and this class is
    the order they run in. The journal it is given is empty at the start and is filled by the
    stages as they go. It prints nothing; the command it is called from does that.
    """

    def __init__(self, loader, journal: Journal):
        self.loader = loader
        self.journal = journal

    def analyze(self) -> Analysis:
        """Every stage, in order, over the runs the modelling can use.

        So far it only sets aside the runs it cannot use.
        """
        runs = Preprocessor(self.journal).run(self.loader.load())

        return Analysis(
            used=[run for run in runs if not self._is_waiting_for_the_lab(run)],
            waiting=[run.run_code for run in runs if self._is_waiting_for_the_lab(run)],
        )

    @staticmethod
    def _is_waiting_for_the_lab(run):
        """True when nothing in the run has come back from the lab yet."""
        return not any(reading.sample and reading.sample.li_mg_l is not None
                       for reading in run.tank_readings)
