"""The modelling, start to finish."""

from dataclasses import dataclass

from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess import Preprocessor
from limodel.models import Run


@dataclass(frozen=True)
class Analysis:
    """What the modelling worked from.

    The runs left out are part of the finding, not a footnote: a polynomial from sixteen
    runs and one from twenty-one are different claims.
    """

    used: list[Run]


class Analyzer:
    """Drives the modelling, from loaded runs to the best setup.

    Each stage lives in its own module and this class is the order they run in. The journal
    it is given is empty at the start and filled as it goes.
    """

    def __init__(self, loader, journal: Journal):
        self.loader = loader
        self.journal = journal

    def analyze(self) -> Analysis:
        """Every stage, in order, over the runs the modelling can use.

        So far it only gets the runs ready; what it finds comes next.
        """
        return Analysis(used=Preprocessor(self.journal).run(self.loader.load()))
