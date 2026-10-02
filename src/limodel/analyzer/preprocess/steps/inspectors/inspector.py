"""The shape every inspector shares."""

from abc import ABC, abstractmethod

from limodel.analyzer.thresholds import Thresholds


class Inspector(ABC):
    """Runs its checks over one part of a run, clearing the values they reject.

    A check is asked for the single worst reading it can see. That value is written down
    and cleared, and the check is asked again -- because the level it compares against is
    better once a bad value is gone. The loop stops when a check finds nothing, or when it
    has cleared as much of one series as it is allowed to.

    Each inspector says which readings of a run it looks at, so a run's tank log and its
    power log are never mixed up.
    """

    def __init__(self, thresholds: Thresholds = Thresholds()):
        self.thresholds = thresholds
        self.checks = self._checks()

    @abstractmethod
    def _checks(self):
        """The checks this inspector runs, in the order they run."""

    @abstractmethod
    def _readings(self, run):
        """The readings of a run this inspector looks at, oldest first."""

    def inspect(self, run, journal):
        """Clears every value this inspector's checks reject, and answers with the readings."""
        readings = self._readings(run)

        for check in self.checks:
            self._clear_what_it_rejects(check, readings, journal)

        return readings

    def _clear_what_it_rejects(self, check, readings, journal):
        """One check, asked again after each value it rejects, until it finds nothing."""
        for _ in range(self._most_it_may_clear(check.judgeable(readings))):
            worst = check.find(readings)
            if worst is None:
                return

            reading, field_name, reason = worst
            journal.skip(reading, field_name, reason)
            setattr(reading, field_name, None)

    def _most_it_may_clear(self, judgeable):
        """How many readings one series may lose before the loop gives up."""
        return max(1, int(len(judgeable) * self.thresholds.most_of_a_series_removable))
