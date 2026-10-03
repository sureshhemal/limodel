"""Everything the fitting made of the runs, carried as one answer."""

from dataclasses import dataclass

from limodel.analyzer.model.best_setup_under_the_gates import BestSetupUnderTheGates
from limodel.analyzer.model.fitted_outcome import FittedOutcome


@dataclass(frozen=True)
class SurrogateModels:
    """What the fitting made of the runs: the fits, the best setups, and what it would not fit.

    The membranes it would not fit are a finding rather than a footnote, because a membrane
    left out with the reason beside it names the next experiment worth running.
    """

    fits: dict[str, dict[str, FittedOutcome]]
    best_setups: dict[str, BestSetupUnderTheGates]
    not_fitted: dict[str, str]
