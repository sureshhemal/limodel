"""BestSetupUnderTheGates: the most selective setup the recovery and voltage gates allow."""

import pytest

from limodel import config

from limodel.analyzer.model.best_setup_under_the_gates import BestSetupUnderTheGates
from limodel.analyzer.model.design_points import DesignPoints
from limodel.analyzer.model.fitted_outcome import FittedOutcome
from limodel.analyzer.model.second_order_polynomial import SecondOrderPolynomial


@pytest.fixture
def points(a_result):
    """Runs at 10 and 20 mA/cm2 against 2 and 8 mol/mol, so coded x1 and x2 are -1 and 1."""
    corners = ((10.0, 2.0), (20.0, 2.0), (10.0, 8.0), (20.0, 8.0))

    return DesignPoints([a_result(run_code=code, current_density_ma_cm2=current,
                                  feed_mg_li_ratio=feed)
                         for code, (current, feed) in zip("ABCD", corners)])


@pytest.fixture
def a_fit():
    """One outcome already fitted, straight from the coefficients a test wants used."""
    def build(field_name, coefficients):
        return FittedOutcome(cem="GO-10", field_name=field_name,
                             polynomial=SecondOrderPolynomial(("intercept", "x1", "x2"),
                                                              coefficients),
                             leave_one_out_rmse=0.0, replicate_spread=None)
    return build


@pytest.fixture
def gates(points, a_fit):
    """Permselectivity 2 + x1 + x2/2, recovery 50 + 10*x1 and voltage 12 + 2*x1."""
    def build(**configuration):
        return BestSetupUnderTheGates(points,
                                      a_fit("permselectivity", (2.0, 1.0, 0.5)),
                                      a_fit("li_recovery_pct", (50.0, 10.0, 0.0)),
                                      a_fit("highest_voltage_v", (12.0, 2.0, 0.0)),
                                      **configuration)
    return build


def test_it_defaults_to_the_gates_the_project_settled_on(gates):
    search = gates()

    assert (search.recovery_floor_pct, search.voltage_ceiling_v) == (35.0, 20.0)


def test_the_answer_is_the_surviving_point_with_the_most_permselectivity(gates):
    """2 + x1 + x2/2 climbs with both settings, so the top corner of the sweep wins."""
    assert gates().find_best_point() == pytest.approx((1.0, 1.0, -1.0))


def test_it_answers_in_the_units_the_bench_is_set_to(gates):
    """Coded 1 and 1 is the strongest current and the highest feed ratio that was run."""
    assert gates().find_settings() == pytest.approx((20.0, 8.0, 1.0))


def test_it_says_what_it_predicts_where_it_lands(gates):
    assert gates().find_best_predictions() == pytest.approx({"permselectivity": 3.5,
                                                             "li_recovery_pct": 60.0,
                                                             "highest_voltage_v": 14.0})


def test_it_sweeps_from_the_lowest_run_to_the_highest_and_no_further(gates):
    levels = gates().find_levels()

    assert (levels[0], levels[-1]) == (-1.0, 1.0)
    assert len(gates().find_coded_grid()) == 21 * 21 * 21


def test_a_recovery_floor_above_everything_predicted_leaves_nothing(gates):
    """The best the fit offers is 60 percent, so a floor of 70 turns every point away."""
    assert gates(recovery_floor_pct=70.0).find_settings() is None


def test_the_recovery_floor_is_named_when_it_did_the_rejecting(gates):
    assert gates(recovery_floor_pct=70.0).find_refusal() == (
        "nothing inside the measured range cleared the lithium recovery floor")


def test_a_voltage_ceiling_below_everything_predicted_leaves_nothing(gates):
    """The gentlest the fit offers is 10 V, so a ceiling of 5 turns every point away."""
    assert gates(voltage_ceiling_v=5.0).find_settings() is None


def test_the_voltage_ceiling_is_named_when_it_did_the_rejecting(gates):
    assert gates(voltage_ceiling_v=5.0).find_refusal() == (
        "nothing inside the measured range cleared the voltage ceiling")


def test_both_gates_are_named_when_both_turned_points_away(gates):
    assert gates(recovery_floor_pct=70.0, voltage_ceiling_v=5.0).find_refusal() == (
        "nothing inside the measured range cleared the lithium recovery floor "
        "and the voltage ceiling")


def test_an_answer_that_got_through_is_not_a_refusal(gates):
    assert gates().find_refusal() is None


def test_a_setup_that_only_just_meets_the_floor_is_kept(gates):
    """50 + 10*x1 reaches exactly 60 at the top, which is not under a floor of 60."""
    assert gates(recovery_floor_pct=60.0).find_settings() == pytest.approx((20.0, 8.0, 1.0))


def test_a_setup_a_hair_under_the_floor_is_turned_away(gates):
    assert gates(recovery_floor_pct=60.001).find_settings() is None


def test_a_gate_leaves_only_the_part_of_the_sweep_that_clears_it(gates):
    """55 percent needs x1 at 0.5 or more: 6 of the 21 levels, at all 21 feed levels."""
    assert len(gates(recovery_floor_pct=55.0).find_survivors()) == 6 * 21 * 21


def test_it_counts_what_each_gate_turned_away(gates):
    assert gates(recovery_floor_pct=55.0).find_rejections() == {
        "lithium recovery floor": 15 * 21 * 21, "voltage ceiling": 0}


@pytest.fixture
def flat(points, a_fit):
    """Permselectivity 2 everywhere, with the same recovery and voltage lines as `gates`."""
    def build(**configuration):
        return BestSetupUnderTheGates(points,
                                      a_fit("permselectivity", (2.0, 0.0, 0.0)),
                                      a_fit("li_recovery_pct", (50.0, 10.0, 0.0)),
                                      a_fit("highest_voltage_v", (12.0, 2.0, 0.0)),
                                      **configuration)
    return build


def test_a_permselectivity_the_same_everywhere_has_no_best_setup(flat):
    """Every surviving point promises 2, so taking the first of them would be a tie-break
    dressed up as a recommendation."""
    assert flat().find_best_point() is None
    assert flat().find_settings() is None


def test_the_tie_is_named_as_the_reason_there_is_no_best_setup(flat):
    assert flat().find_refusal() == (
        "every setup that clears both gates is predicted the same permselectivity, 2.000, "
        "so there is no best one among them")


def test_a_tie_leaves_no_closest_setup_to_show_either(flat):
    """The closest of equals is as arbitrary as the best of them."""
    assert flat(recovery_floor_pct=70.0).find_settings_without_the_gates() is None


def test_a_gate_that_turned_everything_away_is_still_blamed_over_a_tie(flat):
    """With nothing surviving there is no tie to speak of, so the gate is the reason."""
    assert flat(recovery_floor_pct=70.0).find_refusal() == (
        "nothing inside the measured range cleared the lithium recovery floor")


def test_the_tie_rule_absorbs_floating_point_dust_and_nothing_wider(points, a_fit):
    """A millionth of a difference across the sweep is a real slope, not a tie."""
    search = BestSetupUnderTheGates(points, a_fit("permselectivity", (2.0, 1e-6, 0.0)),
                                    a_fit("li_recovery_pct", (50.0, 10.0, 0.0)),
                                    a_fit("highest_voltage_v", (12.0, 2.0, 0.0)))

    assert search.find_best_point() == pytest.approx((1.0, -1.0, -1.0))


def test_an_outcome_that_was_never_fitted_leaves_nothing_to_judge(points, a_fit):
    search = BestSetupUnderTheGates(points, a_fit("permselectivity", None),
                                    a_fit("li_recovery_pct", (50.0, 10.0, 0.0)),
                                    a_fit("highest_voltage_v", (12.0, 2.0, 0.0)))

    assert search.find_settings() is None
    assert search.find_refusal() == "no setup inside the measured range could be predicted"


def test_no_runs_at_all_leaves_the_sweep_nowhere_to_land(a_fit):
    """Without runs there is no range to read a coded point back into real settings."""
    search = BestSetupUnderTheGates(DesignPoints([]),
                                    a_fit("permselectivity", (2.0, 1.0, 0.5)),
                                    a_fit("li_recovery_pct", (50.0, 10.0, 0.0)),
                                    a_fit("highest_voltage_v", (12.0, 2.0, 0.0)))

    assert search.find_settings() is None
    assert search.find_refusal() == (
        "the runs do not cover enough ground to place a setup in real units")


def test_a_single_level_is_not_a_sweep(gates):
    """One level has no span to divide the sweep across, so there is nothing to search."""
    assert gates(steps=1).find_levels() == []
    assert gates(steps=1).find_settings() is None


def test_the_gates_come_from_the_settings_when_it_is_given_none(monkeypatch, gates):
    monkeypatch.setattr(config, "RECOVERY_FLOOR_PCT", 12.5)
    monkeypatch.setattr(config, "VOLTAGE_CEILING_V", 9.5)

    search = gates()

    assert (search.recovery_floor_pct, search.voltage_ceiling_v) == (12.5, 9.5)


def test_what_it_is_given_beats_the_settings(monkeypatch, gates):
    """A caller asking for one floor must get it, whatever the settings say."""
    monkeypatch.setattr(config, "RECOVERY_FLOOR_PCT", 12.5)

    assert gates(recovery_floor_pct=70.0).recovery_floor_pct == 70.0


def test_a_floor_from_the_settings_turns_setups_away(monkeypatch, gates):
    monkeypatch.setattr(config, "RECOVERY_FLOOR_PCT", 70.0)

    assert gates().find_settings() is None


def test_the_best_point_is_still_found_when_every_gate_turns_it_away(gates):
    """Recovery tops out at 60, so a floor of 70 passes nothing, and 70 - 60 is the gap."""
    search = gates(recovery_floor_pct=70.0)

    assert search.find_settings() is None
    assert search.find_settings_without_the_gates() == pytest.approx((20.0, 8.0, 1.0))


def test_the_closest_setting_is_the_most_selective_one_swept(gates):
    """Permselectivity is 2 + x1 + x2/2, highest at the corner where both are +1."""
    found = gates(recovery_floor_pct=70.0).find_predictions_without_the_gates()

    assert found["permselectivity"] == pytest.approx(3.5)
    assert found["li_recovery_pct"] == pytest.approx(60.0)


def test_it_says_how_far_the_closest_setting_misses_the_floor(gates):
    search = gates(recovery_floor_pct=70.0)

    missed = search.find_shortfalls(search.find_best_point_without_the_gates())

    assert missed == {"lithium recovery floor": pytest.approx(10.0)}


def test_it_says_how_far_the_closest_setting_misses_both_gates(gates):
    search = gates(recovery_floor_pct=70.0, voltage_ceiling_v=10.0)

    missed = search.find_shortfalls(search.find_best_point_without_the_gates())

    assert missed == {"lithium recovery floor": pytest.approx(10.0),
                      "voltage ceiling": pytest.approx(4.0)}


def test_a_setting_that_passes_misses_nothing(gates):
    search = gates()

    assert search.find_shortfalls(search.find_best_point()) == {}
