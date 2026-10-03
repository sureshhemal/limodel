"""The runs the modelling can use → one result each."""

from limodel.analyzer.calculate.constants import DILUTE
from limodel.analyzer.calculate.metal import LITHIUM, MAGNESIUM
from limodel.analyzer.calculate.quantities.amount_that_crossed import AmountThatCrossed
from limodel.analyzer.calculate.quantities.balance_gap import BalanceGap
from limodel.analyzer.calculate.quantities.charge_per_lithium_offered import ChargePerLithiumOffered
from limodel.analyzer.calculate.quantities.charge_that_passed import ChargeThatPassed
from limodel.analyzer.calculate.quantities.current_density import CurrentDensity
from limodel.analyzer.calculate.quantities.energy_per_mole_of_lithium import EnergyPerMoleOfLithium
from limodel.analyzer.calculate.quantities.feed_ratio import FeedRatio
from limodel.analyzer.calculate.quantities.lithium_recovery import LithiumRecovery
from limodel.analyzer.calculate.quantities.permselectivity import Permselectivity
from limodel.analyzer.calculate.quantities.stack_voltage import StackVoltage
from limodel.analyzer.calculate.result import Result
from limodel.analyzer.journal import Journal
from limodel.models import Run


class Calculator:
    """One Result per run, for every run whose two outcomes could be worked out.

    Permselectivity and recovery are what the model is fitted to, so a run without them has
    nothing to contribute and is written down as dropped. The diagnostics may be missing on
    a run that is otherwise sound, which is not a reason to let the run go.
    """

    def __init__(self, journal: Journal):
        self.journal = journal

    def find_results(self, runs: list[Run]) -> list[Result]:
        """A result for each run that worked out, in the order the runs arrived."""
        found = [self._find_result(run) for run in runs]

        return [result for result in found if result is not None]

    @staticmethod
    def _find_lithium_offered(run):
        """The millimoles of lithium the dilute started with, which recovery is measured on."""
        ends = AmountThatCrossed.find_ends(run, DILUTE, LITHIUM)

        return None if ends is None else ends[0] / LITHIUM.g_per_mol

    def _find_result(self, run):
        """One run's numbers, or None once the drop is written down."""
        permselectivity = Permselectivity.find_value(run)
        recovery_pct = LithiumRecovery.find_percent(run)
        missing = [name for name, value in (("permselectivity", permselectivity),
                                            ("lithium recovery", recovery_pct))
                   if value is None]

        if missing:
            self.journal.drop(run, f"{' and '.join(missing)} could not be worked out")
            return None

        return Result(run_code=run.run_code,
                      cem=run.cem,
                      current_density_ma_cm2=CurrentDensity.find_ma_per_cm2(run),
                      feed_mg_li_ratio=FeedRatio.find_mg_over_li_from_the_setup(run),
                      charge_per_li_offered=ChargePerLithiumOffered.find_equivalents(run),
                      area_cm2=run.area_cm2,
                      li_feed_mg_l=run.li_feed_mg_l,
                      li_offered_mmol=self._find_lithium_offered(run),
                      cell_pairs=run.cell_pairs,
                      permselectivity=permselectivity,
                      li_recovery_pct=recovery_pct,
                      highest_voltage_v=StackVoltage.find_highest_volts(run),
                      charge_passed_mah_cm2=ChargeThatPassed.find_mah_per_cm2(run),
                      energy_per_mol_li_wh=EnergyPerMoleOfLithium.find_watt_hours(run),
                      li_balance_gap_pct=BalanceGap.find_percent(run, LITHIUM),
                      mg_balance_gap_pct=BalanceGap.find_percent(run, MAGNESIUM))
