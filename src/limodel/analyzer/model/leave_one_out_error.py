"""How far a fit misses the one row it was not shown."""

import math


class LeaveOneOutError:
    """The root mean squared miss when every row takes its turn as the one held back.

    A train and test split measures nothing at this many rows, so the whole set is fitted
    each time but one, and the row left out is the only thing predicted.
    """

    @staticmethod
    def find_rmse(polynomial, coded_rows, outcomes):
        """None when a fold is short of rows, or an outcome is missing."""
        if coded_rows is None or outcomes is None:
            return None

        rows = list(coded_rows)
        values = list(outcomes)

        if len(rows) != len(values) or len(rows) < 2:
            return None

        squares = []

        for left_out in range(len(rows)):
            kept_rows = rows[:left_out] + rows[left_out + 1:]
            kept_values = values[:left_out] + values[left_out + 1:]

            fit = polynomial.find_fit(kept_rows, kept_values)

            if fit is None:
                return None

            prediction = fit.find_prediction(rows[left_out])

            if prediction is None or values[left_out] is None:
                return None

            squares.append((prediction - values[left_out]) ** 2)

        return math.sqrt(sum(squares) / len(squares))
