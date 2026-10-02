"""The power log: the supply and the multimeter."""

from limodel.analyzer.preprocess.steps.checks.instrument import Instrument
from limodel.analyzer.preprocess.steps.checks.paired_values_out_of_proportion import PairedValuesOutOfProportion
from limodel.analyzer.preprocess.steps.checks.paired_values_too_far_apart import PairedValuesTooFarApart
from limodel.analyzer.preprocess.steps.checks.value_far_from_the_median import ValueFarFromTheMedian
from limodel.analyzer.preprocess.steps.inspectors.inspector import Inspector


class PowerLogInspector(Inspector):
    """The voltages and currents written down during a run."""

    def _readings(self, run):
        return sorted(run.stack_readings, key=lambda reading: reading.minute)

    def _checks(self):
        return (
            self._a_current_the_supply_was_not_holding(),
            self._two_voltages_that_do_not_agree(),
            self._two_currents_out_of_proportion(),
        )

    def _a_current_the_supply_was_not_holding(self):
        """The supply holds one current all run, so a reading unlike the rest is wrong."""
        return ValueFarFromTheMedian("supply_current_a", "the supply current", "A",
                                     self.thresholds.impossible_current_share,
                                     self.thresholds.fewest_readings_to_judge)

    def _two_voltages_that_do_not_agree(self):
        """The voltage falls all run, so there is no one level to compare with. What there
        is instead is a second reading of it: the two agree to hundredths of a volt."""
        return PairedValuesTooFarApart(Instrument("supply_voltage_v", "the supply", "V"),
                                       Instrument("meter_voltage_v", "the multimeter", "V"),
                                       "voltage", self.thresholds.largest_voltage_gap_v)

    def _two_currents_out_of_proportion(self):
        """The supply reads about a seventh higher than the multimeter throughout, so the
        two are held against each other as a ratio rather than by subtracting."""
        return PairedValuesOutOfProportion(Instrument("supply_current_a", "the supply", "A"),
                                           Instrument("meter_current_ma", "the multimeter", "mA"),
                                           "current", self.thresholds.plausible_current_ratio,
                                           scale=1000)
