"""Every membrane fitted for all three outcomes, and the best setup each one allows."""

from limodel.analyzer.journal import Journal
from limodel.analyzer.model.best_setup_under_the_gates import (HIGHEST_VOLTAGE, LI_RECOVERY,
                                                               OUTCOME_NAMES, PERMSELECTIVITY,
                                                               BestSetupUnderTheGates)
from limodel.analyzer.model.design_points import DesignPoints
from limodel.analyzer.model.fitted_outcome import FittedOutcome
from limodel.analyzer.model.surrogate_models import SurrogateModels


class Surrogate:
    """Fits all three outcomes of every membrane, then searches each membrane for its setup.

    It writes nothing to the journal: everything it reads is already a Result, and a membrane
    it will not fit is reported on its answer rather than set aside.
    """

    # A fit of an intercept and one slope has two terms, and leave-one-out needs a row to
    # spare, so three runs is the fewest a membrane can be fitted and judged on at all.
    FEWEST_RUNS = 3

    def __init__(self, journal: Journal,
                 recovery_floor_pct=None, voltage_ceiling_v=None):
        self.journal = journal
        self.recovery_floor_pct = recovery_floor_pct
        self.voltage_ceiling_v = voltage_ceiling_v

    def find_models(self, results) -> SurrogateModels:
        """Every membrane's fits and best setup, and the membranes that got neither."""
        fits, best_setups, not_fitted = {}, {}, {}

        for cem, rows in self.find_membranes(results).items():
            refusal = self.find_refusal_for(cem, rows)

            if refusal is not None:
                not_fitted[cem] = refusal
                continue

            fits[cem] = self.find_fits_of(cem, rows)
            missing = [name for name in OUTCOME_NAMES if name not in fits[cem]]

            if missing:
                not_fitted[cem] = f"{cem} had {' and '.join(missing)} that could not be fitted"
                continue

            best_setups[cem] = self.find_best_setup_of(rows, fits[cem])

        return SurrogateModels(fits=fits, best_setups=best_setups, not_fitted=not_fitted)

    def find_membranes(self, results):
        """The runs of each membrane in row order; a run naming no membrane is passed over."""
        membranes = {}

        for result in results:
            if result.cem is None:
                continue

            membranes.setdefault(result.cem, []).append(result)

        return membranes

    def find_refusal_for(self, cem, rows):
        """Why this membrane cannot be fitted at all; None when it can."""
        if len(rows) < self.FEWEST_RUNS:
            return (f"{cem} has too few runs to fit, {len(rows)} against the "
                    f"{self.FEWEST_RUNS} a fit needs")

        points = DesignPoints(rows)

        if points.find_log_rows() is None:
            return f"{cem} has a run with a setting missing or at zero, which has no logarithm"

        # One setting held at one value is dropped and fitted around; both held is no design.
        if points.find_coded_rows() is None:
            return f"{cem} has no setting that varies across its runs, so there is nothing to fit"

        return None

    def find_fits_of(self, cem, rows):
        """Each outcome of one membrane that could be fitted, by the name of the outcome."""
        found = {name: FittedOutcome.find_fit(cem, name, rows) for name in OUTCOME_NAMES}

        return {name: fit for name, fit in found.items() if fit is not None}

    def find_best_setup_of(self, rows, fits):
        """The search over one membrane, bounded by the very rows that were fitted."""
        return BestSetupUnderTheGates(DesignPoints(rows), fits[PERMSELECTIVITY],
                                      fits[LI_RECOVERY], fits[HIGHEST_VOLTAGE],
                                      recovery_floor_pct=self.recovery_floor_pct,
                                      voltage_ceiling_v=self.voltage_ceiling_v)
