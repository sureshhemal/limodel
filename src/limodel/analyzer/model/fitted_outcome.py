"""One outcome of one membrane, fitted, with everything a reader needs to judge it."""

from dataclasses import dataclass

from limodel.analyzer.model.design_points import DesignPoints
from limodel.analyzer.model.leave_one_out_error import LeaveOneOutError
from limodel.analyzer.model.replicate_scatter import ReplicateScatter
from limodel.analyzer.model.second_order_polynomial import (INTERCEPT,
                                                            SecondOrderPolynomial,
                                                            find_term_names)

SQUARED = "_squared"

# The terms the search may offer, scanned in this order so a tie goes to the simpler one.
# There is no x1*x2 among them, and that is a decision rather than an oversight: the runs move
# current density only at the lowest feed ratio and feed ratio only at one current density, so
# an interaction between them has no support in this data.
CANDIDATE_TERMS = tuple(name for name in find_term_names(len(DesignPoints.SETTING_NAMES))
                        if name != INTERCEPT)


@dataclass(frozen=True)
class FittedOutcome:
    """What one outcome of one membrane came out as: the terms that earned their place.

    The leave-one-out error and the replicate spread travel with the coefficients because an
    equation on its own cannot be judged: a fit that misses by more than the bench's own
    scatter has learnt nothing the repeats did not already say.
    """

    cem: str
    field_name: str
    polynomial: SecondOrderPolynomial
    leave_one_out_rmse: float
    replicate_spread: tuple[float, int] | None

    def find_prediction(self, coded_row):
        """What this outcome comes to at one coded point."""
        return self.polynomial.find_prediction(coded_row)

    def find_terms_and_coefficients(self):
        """The surviving terms with their coefficients, in order, for the report to print."""
        return self.polynomial.find_terms_and_coefficients()

    @staticmethod
    def find_fit(cem, field_name, results):
        """This outcome fitted over these runs; None when they cannot settle even a mean."""
        points = DesignPoints(results)
        coded_rows = points.find_coded_rows()
        coded_names = points.find_usable_coded_names()
        outcomes = [getattr(result, field_name, None) for result in results]

        if coded_rows is None or coded_names is None:
            return None

        candidates = FittedOutcome.find_candidates_on(coded_names)
        best = FittedOutcome.find_best_polynomial(coded_rows, outcomes, candidates)

        if best is None:
            return None

        rmse, polynomial = best
        fitted = polynomial.find_fit(coded_rows, outcomes)

        if fitted is None:
            return None

        return FittedOutcome(cem, field_name, fitted, rmse,
                             ReplicateScatter(field_name).find_spread(results))

    @staticmethod
    def find_candidates_on(coded_names):
        """The candidate terms built on a setting that varies, in the order they are tried."""
        return tuple(name for name in CANDIDATE_TERMS
                     if name.removesuffix(SQUARED) in coded_names)

    @staticmethod
    def find_best_polynomial(coded_rows, outcomes, candidates=CANDIDATE_TERMS):
        """The error and the terms it belongs to, grown one forward step at a time."""
        chosen = (INTERCEPT,)
        rmse = LeaveOneOutError.find_rmse(SecondOrderPolynomial(chosen), coded_rows, outcomes)

        if rmse is None:
            return None

        while True:
            addition = FittedOutcome.find_best_addition(chosen, candidates, coded_rows, outcomes)

            # Nothing left that lowers the error is where the model stops growing.
            if addition is None or addition[0] >= rmse:
                return rmse, SecondOrderPolynomial(chosen)

            rmse, chosen = addition

    @staticmethod
    def find_best_addition(chosen, candidates, coded_rows, outcomes):
        """The lowest error one more term reaches, with the terms that reach it; None if none."""
        best = None

        for name in FittedOutcome.find_terms_it_may_add(chosen, candidates):
            terms = chosen + (name,)
            rmse = LeaveOneOutError.find_rmse(SecondOrderPolynomial(terms), coded_rows, outcomes)

            # No error means these rows cannot settle that term, so it cannot be judged at all.
            if rmse is None or (best is not None and rmse >= best[0]):
                continue

            best = (rmse, terms)

        return best

    @staticmethod
    def find_terms_it_may_add(chosen, candidates=CANDIDATE_TERMS):
        """The candidates not in the model yet whose own linear term already is."""
        allowed = []

        for name in candidates:
            linear = name.removesuffix(SQUARED)

            # A curve without its slope cannot be read, so a squared term waits for its own.
            if name in chosen or (linear != name and linear not in chosen):
                continue

            allowed.append(name)

        return tuple(allowed)
