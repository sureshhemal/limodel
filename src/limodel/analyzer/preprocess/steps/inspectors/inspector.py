"""The shape every inspector shares."""

from abc import ABC, abstractmethod

from limodel.analyzer.thresholds import Thresholds


class Inspector(ABC):
    """Runs its checks over one part of a run, clearing the values they reject.

    A check is asked for the worst reading it can see. That value is written down, cleared,
    and the check asked again, because the level it compares against is better once a bad
    value is gone.
    """

    def __init__(self, thresholds: Thresholds = Thresholds()):
        self.thresholds = thresholds
        self.checks = self._find_checks()

    @abstractmethod
    def _find_checks(self):
        """The checks this inspector runs, in the order they run."""

    @abstractmethod
    def _find_readings(self, run):
        """The readings of a run this inspector looks at, oldest first."""

    def inspect(self, run, journal):
        """Clears every value this inspector's checks reject, and answers with the readings."""
        readings = self._find_readings(run)

        for check in self.checks:
            self._clear_what_it_rejects(check, readings, journal)

        return readings

    def _clear_what_it_rejects(self, check, readings, journal):
        """One check, asked again after each value it rejects, until it finds nothing."""
        for _ in range(self._find_clearing_limit(check.find_judgeable_readings(readings))):
            worst = check.find_worst_offender(readings)
            if worst is None:
                return

            reading, field_name, reason = worst
            journal.skip(reading, field_name, reason)
            setattr(reading, field_name, None)

    def _find_clearing_limit(self, judgeable):
        """How many readings one series may lose before the loop gives up."""
        return max(1, int(len(judgeable) * self.thresholds.most_of_a_series_removable))
