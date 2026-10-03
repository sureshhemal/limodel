"""Calculator: a result for each run the model can fit, and a journalled drop for the rest."""

import pytest

from limodel.analyzer.calculate.calculator import Calculator
from limodel.analyzer.calculate.constants import DILUTE
from limodel.analyzer.calculate.result import Result
from limodel.analyzer.journal import Journal


@pytest.fixture
def a_sound_run(a_run, a_sampled_reading, a_stack_reading):
    """A run of round numbers that every quantity can be worked out from.

    Every tank is 100 g of tare under 1100 g, so 1.000 L and a mg/L figure reads straight as
    milligrams. The concentrate gains 69.4 mg of Li and 243.05 mg of Mg, 10 mmol of each,
    out of a feed holding 100 mmol/L of each, over an hour at 10 V and 0.1 A.
    """
    def build(run_code="AA", dilute_li_at_the_end=555.2, dilute_mg_at_the_end=1944.4):
        return a_run(run_code=run_code, li_feed_mg_l=69.4, mg_feed_mg_l=243.05,
                     tank_readings=(
                         a_sampled_reading(run_code=run_code, minute=0, weight_g=1100,
                                           li_mg_l=10, mg_mg_l=10),
                         a_sampled_reading(run_code=run_code, minute=60, weight_g=1100,
                                           li_mg_l=79.4, mg_mg_l=253.05),
                         a_sampled_reading(run_code=run_code, tank=DILUTE, minute=0,
                                           weight_g=1100, li_mg_l=694, mg_mg_l=2430.5),
                         a_sampled_reading(run_code=run_code, tank=DILUTE, minute=60,
                                           weight_g=1100, li_mg_l=dilute_li_at_the_end,
                                           mg_mg_l=dilute_mg_at_the_end)),
                     stack_readings=(
                         a_stack_reading(run_code=run_code, minute=0, supply_voltage_v=10,
                                         supply_current_a=0.1),
                         a_stack_reading(run_code=run_code, minute=60, supply_voltage_v=10,
                                         supply_current_a=0.1)))
    return build


def test_it_gives_a_sound_run_the_two_outcomes_the_model_is_fitted_to(a_sound_run):
    """t_li/t_mg of 0.5 over a feed ratio of 1.0, and 69.4 of the feed's 694 mg of Li."""
    result, = Calculator(Journal()).find_results([a_sound_run()])

    assert result.permselectivity == pytest.approx(0.5)
    assert result.li_recovery_pct == pytest.approx(10.0)


def test_it_gives_a_sound_run_the_two_settings_it_was_run_at(a_sound_run):
    """0.1 A over 10 cm2, and a feed of 10 mmol/L of Mg to 10 of Li."""
    result, = Calculator(Journal()).find_results([a_sound_run()])

    assert result.current_density_ma_cm2 == pytest.approx(10.0)
    assert result.feed_mg_li_ratio == pytest.approx(1.0)


def test_it_gives_a_sound_run_its_diagnostics(a_sound_run):
    """360 C over 10 cm2 is 10 mAh/cm2, and 3600 J over 0.01 mol of Li is 100 Wh/mol."""
    result, = Calculator(Journal()).find_results([a_sound_run()])

    assert result.highest_voltage_v == pytest.approx(10.0)
    assert result.charge_passed_mah_cm2 == pytest.approx(10.0)
    assert result.energy_per_mol_li_wh == pytest.approx(100.0)


def test_the_balance_gaps_are_the_share_of_the_loss_that_was_never_found(a_sound_run):
    """The feed lost 138.8 mg of Li and the concentrate gained 69.4 of it: half went astray."""
    result, = Calculator(Journal()).find_results([a_sound_run()])

    assert result.li_balance_gap_pct == pytest.approx(50.0)
    assert result.mg_balance_gap_pct == pytest.approx(50.0)


def test_a_result_is_named_after_the_run_it_came_from(a_sound_run):
    result, = Calculator(Journal()).find_results([a_sound_run()])

    assert isinstance(result, Result)
    assert result.run_code == "AA"
    assert result.cem == "GO-10"


def test_a_run_the_lab_never_reported_is_not_given_a_result(a_run, a_stack_reading):
    """With no samples there is neither a crossing to measure nor a feed to measure it by."""
    run = a_run(stack_readings=(a_stack_reading(minute=0, supply_voltage_v=10,
                                                supply_current_a=0.1),))

    assert Calculator(Journal()).find_results([run]) == []


def test_a_dropped_run_is_written_down_with_what_was_missing(a_run):
    journal = Journal()

    Calculator(journal).find_results([a_run()])

    assert [(entry.id, entry.model, entry.reason) for entry in journal.entries] == [
        ("AA", "Run", "permselectivity and lithium recovery could not be worked out")]


def test_a_metal_the_lab_never_reported_loses_the_run(a_run, a_sampled_reading):
    """Permselectivity needs both metals, and one missing is enough to lose the run."""
    run = a_run(tank_readings=(
        a_sampled_reading(minute=0, weight_g=1100, li_mg_l=10, mg_mg_l=None),
        a_sampled_reading(minute=60, weight_g=1100, li_mg_l=79.4, mg_mg_l=None),
        a_sampled_reading(tank=DILUTE, minute=0, weight_g=1100, li_mg_l=694, mg_mg_l=2430.5),
        a_sampled_reading(tank=DILUTE, minute=60, weight_g=1100, li_mg_l=555.2,
                          mg_mg_l=1944.4)))
    journal = Journal()

    results = Calculator(journal).find_results([run])

    assert results == []
    assert [entry.reason for entry in journal.entries] == [
        "permselectivity could not be worked out"]


def test_one_sampled_minute_in_the_concentrate_is_too_few_to_work_from(a_run,
                                                                      a_sampled_reading):
    """A crossing is a difference between two minutes, so a tank sampled once has none."""
    run = a_run(tank_readings=(
        a_sampled_reading(minute=60, weight_g=1100, li_mg_l=79.4, mg_mg_l=253.05),
        a_sampled_reading(tank=DILUTE, minute=0, weight_g=1100, li_mg_l=694, mg_mg_l=2430.5),
        a_sampled_reading(tank=DILUTE, minute=60, weight_g=1100, li_mg_l=555.2,
                          mg_mg_l=1944.4)))
    journal = Journal()

    results = Calculator(journal).find_results([run])

    assert results == []
    assert [entry.reason for entry in journal.entries] == [
        "permselectivity and lithium recovery could not be worked out"]


def test_a_feed_that_held_no_lithium_loses_the_run(a_run, a_sampled_reading, a_stack_reading):
    """Recovery and the feed ratio both divide by it, and nothing can be divided by zero."""
    run = a_run(tank_readings=(
        a_sampled_reading(minute=0, weight_g=1100, li_mg_l=10, mg_mg_l=10),
        a_sampled_reading(minute=60, weight_g=1100, li_mg_l=79.4, mg_mg_l=253.05),
        a_sampled_reading(tank=DILUTE, minute=0, weight_g=1100, li_mg_l=0, mg_mg_l=2430.5),
        a_sampled_reading(tank=DILUTE, minute=60, weight_g=1100, li_mg_l=0,
                          mg_mg_l=1944.4)))

    assert Calculator(Journal()).find_results([run]) == []


def test_a_run_whose_balance_gap_cannot_be_worked_out_is_still_kept(a_sound_run):
    """A feed that ends where it started lost nothing to divide by; the outcomes stand."""
    run = a_sound_run(dilute_li_at_the_end=694, dilute_mg_at_the_end=2430.5)
    journal = Journal()

    result, = Calculator(journal).find_results([run])

    assert result.li_balance_gap_pct is None
    assert result.mg_balance_gap_pct is None
    assert result.li_recovery_pct == pytest.approx(10.0)
    assert journal.entries == ()


def test_no_runs_at_all_is_not_an_error():
    assert Calculator(Journal()).find_results([]) == []


def test_the_results_come_back_in_the_order_the_runs_arrived(a_sound_run):
    runs = [a_sound_run(run_code="BB"), a_sound_run(run_code="AA")]

    results = Calculator(Journal()).find_results(runs)

    assert [result.run_code for result in results] == ["BB", "AA"]


def test_a_dropped_run_leaves_the_others_their_results(a_sound_run, a_run):
    journal = Journal()

    results = Calculator(journal).find_results([a_run(run_code="CC"), a_sound_run()])

    assert [result.run_code for result in results] == ["AA"]
    assert [entry.id for entry in journal.entries] == ["CC"]


def test_nothing_is_written_down_when_every_run_works_out(a_sound_run):
    journal = Journal()

    Calculator(journal).find_results([a_sound_run(), a_sound_run(run_code="BB")])

    assert journal.entries == ()


def test_the_runs_it_is_given_are_not_changed(a_sound_run):
    run = a_sound_run()
    before = run.model_copy(deep=True)

    Calculator(Journal()).find_results([run])

    assert run == before
