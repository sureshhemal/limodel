"""Step 3: dropping the runs the lab cannot answer for."""

from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess.steps.step import Step
from limodel.models import Run

# the rinse is not part of the chemistry, so it is not asked for
TANKS_THE_MODELLING_NEEDS = ("conc", "dil")

# permselectivity is a ratio of ratios, so both metals are needed, not lithium alone
METALS_THE_MODELLING_NEEDS = ("li_mg_l", "mg_mg_l")


class DropRunsMissingAnEndSample(Step):
    """Keeps the runs the lab has answered for.

    A run needs both metals, in both tanks, at its first sampled minute and its last. The
    samples in between are not asked for. It runs after the readings are checked, so a run
    on its way out is still looked over.
    """

    name = "no lab results at both ends"

    def apply(self, runs: list[Run], journal: Journal) -> list[Run]:
        return [run for run in runs if self._the_lab_has_answered_for(run)]

    def _the_lab_has_answered_for(self, run):
        """True when every tank the modelling needs has both of its ends measured."""
        return all(self._both_ends_are_measured(run, tank) for tank in TANKS_THE_MODELLING_NEEDS)

    def _both_ends_are_measured(self, run, tank):
        sampled = self._find_sampled_readings(run, tank)
        if len(sampled) < 2:
            return False

        return all(self._the_lab_has_reported(reading.sample) for reading in (sampled[0], sampled[-1]))

    @staticmethod
    def _find_sampled_readings(run, tank):
        """One tank's readings that a sample was drawn from, oldest first."""
        return sorted((reading for reading in run.tank_readings
                       if reading.tank == tank and reading.sample),
                      key=lambda reading: reading.minute)

    @staticmethod
    def _the_lab_has_reported(sample):
        """True when the lab has reported every metal the modelling needs."""
        return all(getattr(sample, metal) is not None for metal in METALS_THE_MODELLING_NEEDS)
