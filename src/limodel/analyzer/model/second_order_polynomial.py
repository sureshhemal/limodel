"""A quadratic in the coded settings, fitted by least squares."""

import numpy as np

INTERCEPT = "intercept"
SQUARED = "_squared"


def find_term_names(settings):
    """Every term available over this many coded settings, the simplest ones first."""
    coded = tuple(f"x{at + 1}" for at in range(settings))

    return (INTERCEPT, *coded, *(name + SQUARED for name in coded))


# No term multiplies one setting by another, and that is a decision rather than an oversight:
# the runs move each setting only while the others sit still, so a product of two of them
# carries nothing the two columns do not already carry.


class SecondOrderPolynomial:
    """The terms a fit may use, and the coefficients it came back with once fitted.

    Fitting returns a new polynomial rather than filling this one in, so leave-one-out can
    fit the same terms many times over without the folds treading on each other.
    """

    def __init__(self, term_names, coefficients=None):
        self.term_names = tuple(term_names)
        self.coefficients = coefficients

    def find_fit(self, coded_rows, outcomes):
        """These terms with coefficients; None when the rows cannot settle every one."""
        columns = self.find_term_columns(coded_rows)
        values = self.find_outcome_values(outcomes)

        if columns is None or values is None or len(columns) != len(values):
            return None

        if len(columns) < len(self.term_names):
            return None

        coefficients, _, rank, _ = np.linalg.lstsq(columns, values, rcond=None)

        # A rank short of the terms means two of them move together across these rows, so no
        # one set of coefficients is the answer.
        if rank < len(self.term_names):
            return None

        return SecondOrderPolynomial(self.term_names, tuple(float(each) for each in coefficients))

    def find_prediction(self, coded_row):
        """None until the polynomial has been fitted."""
        row = self.find_term_row(coded_row)

        if self.coefficients is None or row is None:
            return None

        return sum(coefficient * value
                   for coefficient, value in zip(self.coefficients, row))

    def find_terms_and_coefficients(self):
        """Each term with its coefficient, in order, so the report can print the equation."""
        if self.coefficients is None:
            return None

        return tuple(zip(self.term_names, self.coefficients))

    def find_term_columns(self, coded_rows):
        """One column per term and one row per coded point; None when a point is unusable."""
        if coded_rows is None:
            return None

        rows = []

        for coded_row in coded_rows:
            row = self.find_term_row(coded_row)

            if row is None:
                return None

            rows.append(row)

        if not rows:
            return None

        return np.array(rows, dtype=float)

    def find_term_row(self, coded_row):
        """What each term works out to at one coded point; None on a term it does not know."""
        if not self.term_names or coded_row is None:
            return None

        if any(value is None for value in coded_row):
            return None

        row = [self.find_term_value(name, coded_row) for name in self.term_names]

        return None if any(value is None for value in row) else tuple(row)

    @staticmethod
    def find_term_value(name, coded_row):
        """One term at one point; None when the name is not a term of a point this wide."""
        if name == INTERCEPT:
            return 1.0

        base = name.removesuffix(SQUARED)

        if len(base) < 2 or base[0] != "x" or not base[1:].isdigit():
            return None

        at = int(base[1:]) - 1

        if not 0 <= at < len(coded_row):
            return None

        return coded_row[at] ** 2 if name.endswith(SQUARED) else coded_row[at]

    def find_outcome_values(self, outcomes):
        """None when an outcome is missing, because a gap cannot be fitted around."""
        if outcomes is None:
            return None

        values = list(outcomes)

        if not values or any(value is None for value in values):
            return None

        return np.array(values, dtype=float)
