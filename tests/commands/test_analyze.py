"""The analyze command: what it left out, what it calculated, and what it fitted."""

from types import SimpleNamespace

import itertools
import re

import pytest
from typer.testing import CliRunner

from limodel import config
from limodel.analyzer import Journal
from limodel.cli.commands.analyze import Analyze
from limodel.cli.main import app
from limodel.models import Run, Sample, StackReading, TankReading

runner = CliRunner()

TARE_G = 100.0
WEIGHT_G = 2100.0     # 2.000 L in a tank tared at 100 g
LAST_MINUTE = 240
VOLTS = 16.0


def find_line(lines, holding):
    """The one printed line that holds this text."""
    return next(line for line in lines if holding in line)


def find_index(lines, holding):
    """Where the first line holding this text was printed."""
    return next(at for at, line in enumerate(lines) if holding in line)


def find_row(lines, run_code):
    """The table line of one run, split into its cells."""
    return next(line.split() for line in lines if line.split()[:1] == [run_code])


@pytest.fixture
def analyze(monkeypatch, data_dir):
    def run(into=data_dir):
        monkeypatch.setattr(config, "DATA_SOURCE", "csv")
        monkeypatch.setattr(config, "DATA_DIR", into)
        return runner.invoke(app, ["analyze"])
    return run


@pytest.fixture
def a_sampled_reading():
    """One tank reading with its lab sample, both at the same minute."""
    def build(tank, minute, li_mg_l, mg_mg_l, run_code):
        sample = Sample(sample_id=f"{run_code}-{tank}-{minute}", run_code=run_code,
                        minute=minute, tank=tank, li_mg_l=li_mg_l, mg_mg_l=mg_mg_l)

        return TankReading(run_code=run_code, minute=minute, tank=tank, weight_g=WEIGHT_G,
                           sample=sample)
    return build


@pytest.fixture
def a_run(a_sampled_reading):
    """A run built from round values, so every number the report prints is exact.

    Each tank holds 2.000 L. The concentrate gains 69.4 mg of lithium, which is 10 mmol, and
    121.525 mg of magnesium, which is 5 mmol and the same charge, so t_li/t_mg is 1. The
    dilute starts with 10 mmol/L of each metal, so the feed ratio permselectivity divides by
    is 1 and permselectivity itself is 1.000. The dilute starts with 138.8 mg of lithium and
    the concentrate takes 69.4 of it, so recovery is 50.0 %, and every milligram the dilute
    lost is found in the concentrate, so both balance gaps are 0.0.
    """
    def build(run_code="AA", cem="GO-10", supply_current_a=0.1, mg_feed_mg_l=2430.5,
              dil_li_mg_l=69.4, minutes=(0, LAST_MINUTE), include=True, li_feed_mg_l=694.0):
        tank_readings = [a_sampled_reading("conc", 0, 0.0, 0.0, run_code),
                         a_sampled_reading("conc", LAST_MINUTE, 34.7, 60.7625, run_code),
                         a_sampled_reading("dil", 0, dil_li_mg_l, 243.05, run_code),
                         a_sampled_reading("dil", LAST_MINUTE, 34.7, 182.2875, run_code)]
        stack_readings = [StackReading(run_code=run_code, minute=minute, supply_voltage_v=VOLTS,
                                       supply_current_a=supply_current_a)
                          for minute in minutes]

        return Run(run_code=run_code, series="new_set_mg", run_date="2026-07-09", cem=cem,
                   aem="AR 204", li_feed_mg_l=li_feed_mg_l, mg_feed_mg_l=mg_feed_mg_l,
                   conc_start_salt="LiCl", conc_start_g_l=0.5, rinse_salt="Na2SO4",
                   rinse_wt_pct=2, flow_l_min=0.2, area_cm2=10.0, cell_pairs=10,
                   tare_conc_g=TARE_G, tare_dil_g=TARE_G, tare_rinse_g=TARE_G,
                   include=include, tank_readings=tank_readings,
                   stack_readings=stack_readings)
    return build


@pytest.fixture
def three_runs(a_run):
    """One membrane at 10, 20 and 40 mA/cm2 against feeds of 1, 2 and 4 mol/mol."""
    def build():
        return [a_run(run_code="AA", supply_current_a=0.1, mg_feed_mg_l=2430.5),
                a_run(run_code="BB", supply_current_a=0.2, mg_feed_mg_l=4861.0),
                a_run(run_code="CC", supply_current_a=0.4, mg_feed_mg_l=9722.0)]
    return build


@pytest.fixture
def four_runs_at_one_feed(a_run):
    """10, 20, 40 and 20 mA/cm2, every run at a feed of 1 mol/mol, so the 20s repeat.

    A dilute starting at 69.4 mg/L recovers 50 % and one starting at 34.7 mg/L recovers
    100 %, so the four runs come out at 50, 100, 50 and 100 and the two 20s agree exactly.
    """
    def build():
        return [a_run(run_code="AA", supply_current_a=0.1, dil_li_mg_l=69.4),
                a_run(run_code="BB", supply_current_a=0.2, dil_li_mg_l=34.7),
                a_run(run_code="CC", supply_current_a=0.4, dil_li_mg_l=69.4),
                a_run(run_code="DD", supply_current_a=0.2, dil_li_mg_l=34.7)]
    return build


@pytest.fixture
def a_command():
    """The command over runs handed straight to it, with nothing on disk."""
    def build(runs):
        return Analyze(SimpleNamespace(load=lambda: list(runs), find_refused_rows=tuple), Journal())
    return build


@pytest.fixture
def report(a_command, capsys, monkeypatch):
    """Every line the command printed over those runs.

    Preprocessing drops a run on a membrane that is not being modelled, so a test about what
    the report prints has to model whatever membranes it put in.
    """
    def run(runs, membranes=None):
        monkeypatch.setattr(config, "MEMBRANES_MODELLED",
                            tuple(membranes) if membranes else tuple({run.cem for run in runs}))
        a_command(runs).run()

        return capsys.readouterr().out.splitlines()
    return run


def test_analyze_counts_the_runs_it_can_use(analyze):
    result = analyze()

    assert result.exit_code == 0
    assert "using 2 of 2 runs" in result.output
    assert "dropped" not in result.output


def test_analyze_names_a_run_the_lab_has_not_finished_with(analyze, write_file, fixture_text):
    data_dir = write_file("samples.csv", fixture_text("samples.csv").replace("BB1,BB,0,conc,60,3",
                                                                            "BB1,BB,0,conc,,"))

    result = analyze(into=data_dir)

    assert result.exit_code == 0
    assert "using 1 of 2 runs" in result.output
    assert "dropped  run      BB             no lab results at both ends" in result.output


def test_analyze_leaves_out_a_run_marked_not_to_be_used(analyze, write_file, fixture_text):
    data_dir = write_file("runs.csv", fixture_text("runs.csv").replace("42,true,", "42,false,"))

    result = analyze(into=data_dir)

    assert result.exit_code == 0
    assert "dropped  run      AA             not marked for use" in result.output
    assert "using 1 of 2 runs" in result.output


def test_analyze_tables_the_runs_it_calculated(analyze):
    result = analyze()

    assert result.exit_code == 0
    assert "recovery %" in result.output


def test_it_heads_the_table_with_the_name_of_every_column(report, a_run):
    lines = report([a_run()])

    assert find_line(lines, "recovery %").split() == ["run", "membrane", "mA/cm2", "Mg/Li",
                                                      "perm", "recovery", "%", "volts",
                                                      "mAh/cm2", "Li", "gap", "%", "Mg",
                                                      "gap", "%"]


def test_it_prints_every_number_of_a_run_it_calculated(report, a_run):
    """10 mA/cm2 held for 240 minutes is 40 mAh/cm2, and the rest is the fixture's own."""
    lines = report([a_run()])

    assert find_row(lines, "AA") == ["AA", "GO-10", "10.00", "1.00", "1.000", "50.0", "16.0",
                                     "40.0", "0.0", "0.0"]


def test_a_number_that_could_not_be_worked_out_prints_as_a_dash(report, a_run):
    """One minute of the power log is no interval, so there is no charge under it."""
    lines = report([a_run(minutes=(0,))])

    assert find_row(lines, "AA")[7] == "-"
    assert "None" not in "\n".join(lines)


def test_it_names_a_run_whose_diagnostics_are_missing(report, a_run):
    lines = report([a_run(minutes=(0,))])

    assert lines[-1] == "diagnostics missing on AA"


def test_a_run_with_every_diagnostic_is_not_called_thin(report, a_run):
    assert "diagnostics missing" not in "\n".join(report([a_run()]))


def test_what_was_left_out_comes_before_any_number(report, a_run):
    lines = report([a_run(run_code="AA", include=False), a_run(run_code="BB")])

    assert find_index(lines, "not marked for use") < find_index(lines, "using 1 of 2 runs")
    assert find_index(lines, "using 1 of 2 runs") < find_index(lines, "recovery %")


def test_a_run_whose_numbers_divide_by_zero_is_named_rather_than_tabled(report, a_run):
    """A dilute reported with no lithium leaves recovery nothing to measure against."""
    lines = report([a_run(dil_li_mg_l=0.0)])

    assert "permselectivity and lithium recovery could not be worked out" in lines[0]
    assert lines[-1] == "using 1 of 1 runs"


def test_no_runs_at_all_prints_the_count_and_nothing_else(report):
    assert report([]) == ["using 0 of 0 runs"]


def test_it_prints_the_terms_that_survived_for_each_outcome(report, three_runs):
    """Every run came out at 50 % recovery, so the intercept is the 50 they all sat at."""
    lines = report(three_runs())

    assert find_line(lines, "intercept +50").startswith("  recovery %")


def test_it_prints_the_error_beside_the_scatter_it_is_judged_against(report, three_runs):
    """No setup was run twice here, so there is no bench scatter to hold the error against."""
    lines = report(three_runs())

    assert "off by 0.000, with no setup run twice to judge it against" in find_line(lines,
                                                                                    "off by")


def test_the_bench_scatter_is_printed_when_a_setup_was_run_twice(report, three_runs, a_run):
    """DD repeats AA setting for setting and came out the same, so the pair scatters by 0."""
    lines = report([*three_runs(), a_run(run_code="DD")])
    judgement = find_line(lines, "bench scatter")

    assert "against a bench scatter of 0.000 from 1 repeat" in judgement
    assert "earned no conclusion" not in judgement


def test_a_fit_that_misses_by_more_than_the_bench_scatter_is_called_out(
        report, four_runs_at_one_feed):
    """The mean of 50, 100, 50 and 100 is 75, and no slope fits a recovery that goes up
    then down, so leave-one-out misses by 33.333 against repeats that agreed exactly."""
    lines = report(four_runs_at_one_feed())
    judgement = lines[find_index(lines, "intercept +75") + 1]

    assert "off by 33.333 against a bench scatter of 0.000 from 1 repeat" in judgement
    assert "worse than the bench repeating itself" in judgement
    assert "earned no conclusion" in judgement


def test_it_prints_the_best_setup_under_the_gates_in_real_units(report, three_runs):
    """The sweep works in coded units, so the answer has to be read back in real ones, and
    only inside the 10 to 40 mA/cm2 and 1 to 4 mol/mol the runs covered."""
    said = find_line(report(three_runs()), "best setup")
    current, feed = re.search(r"([\d.]+) mA/cm2 at a feed of ([\d.]+) mol/mol", said).groups()

    assert 10.0 <= float(current) <= 40.0
    assert 1.0 <= float(feed) <= 4.0
    assert "equivalents per lithium" in said


def test_it_quotes_what_the_best_setup_is_predicted_to_give(report, three_runs):
    lines = report(three_runs())
    promise = lines[find_index(lines, "best setup") + 1]

    assert "permselectivity 1.000" in promise
    assert "recovery % 50.000" in promise
    assert "volts 16.000" in promise


def test_a_membrane_with_too_few_runs_prints_its_name_and_the_reason(report, a_run):
    """One run cannot fit even a mean and leave a row over to judge it on."""
    lines = report([a_run()])

    assert "GO-10" in lines
    assert "too few runs to fit, 1 against the 3 a fit needs" in find_line(lines, "not fitted")


def test_a_membrane_whose_settings_never_varied_prints_the_reason(report, a_run):
    lines = report([a_run(run_code=code) for code in ("AA", "BB", "CC")])

    assert "no setting that varies across its runs" in find_line(lines, "not fitted")


def test_it_names_both_settings_a_fit_was_made_in(report, three_runs):
    """These runs move current density from 10 to 40 and the feed from 1 to 4."""
    lines = report(three_runs())

    assert "current density and the feed ratio" in find_line(lines, "fitted in")
    assert "never tested" not in find_line(lines, "fitted in")


def test_a_setting_held_at_one_value_is_named_as_never_tested(report, four_runs_at_one_feed):
    """A reader who sees a fit in current density must not read the feed as tested."""
    lines = report(four_runs_at_one_feed())
    fitted_in = find_line(lines, "fitted in")

    assert "current density" in fitted_in
    assert "the feed ratio held at one value across these runs and never tested" in fitted_in


def test_a_membrane_that_was_not_fitted_names_no_settings(report, a_run):
    lines = report([a_run()])

    assert "fitted in" not in "\n".join(lines)


def test_a_membrane_name_wider_than_its_heading_does_not_shove_the_table_right(report, a_run):
    """The name is 15 characters against a heading of 8, so the column has to grow to 15."""
    lines = report([a_run(run_code="AA", cem="PDA/PEI/15CE/BT"), a_run(run_code="BB")])

    assert find_line(lines, "recovery %").startswith("run  membrane         mA/cm2")
    assert find_row(lines, "AA")[1] == "PDA/PEI/15CE/BT"
    assert (find_line(lines, "PDA/PEI/15CE/BT").index("10.00")
            == find_line(lines, "GO-10").index("10.00"))


def test_it_hands_back_the_analysis_it_printed(a_command, a_run):
    analysis = a_command([a_run()]).run()

    assert [result.run_code for result in analysis.results] == ["AA"]
    assert "GO-10" in analysis.models.not_fitted


def test_the_table_is_followed_by_what_its_columns_mean(report, three_runs):
    lines = report(three_runs())

    assert find_index(lines, "what the columns mean") > find_index(lines, "recovery %")


def test_a_gate_says_what_passes_it(report, three_runs):
    lines = report(three_runs())

    assert "35 % or more passes" in find_line(lines, "a gate: the share")
    assert "20 V or less passes" in find_line(lines, "the highest the supply reached")


def test_the_measure_being_maximised_says_where_no_preference_sits(report, three_runs):
    """A reader cannot judge 2.498 without knowing the number that means no preference."""
    lines = report(three_runs())

    assert "0.5 is no preference" in find_line(lines, "what the model maximises")


def find_legend(lines):
    """Just the lines under the legend heading, up to the blank that ends it."""
    after = lines[find_index(lines, "what the columns mean") + 1:]

    return list(itertools.takewhile(lambda line: line.strip(), after))


def test_a_column_of_words_is_not_explained(report, three_runs):
    """The run code and the membrane name say what they are; a line each would be noise."""
    explained = [line.split()[0] for line in find_legend(report(three_runs()))]

    assert "run" not in explained and "membrane" not in explained


def test_nothing_is_explained_when_no_run_was_calculated(report):
    """With no table there are no columns, so the legend would be explaining nothing."""
    assert "what the columns mean" not in "\n".join(report([]))


def test_the_legend_quotes_the_gates_that_are_really_in_force(monkeypatch, report, three_runs):
    """A floor is a setting, so a legend naming 35 would be lying once it is changed."""
    monkeypatch.setattr(config, "RECOVERY_FLOOR_PCT", 28.0)
    monkeypatch.setattr(config, "VOLTAGE_CEILING_V", 16.0)

    lines = report(three_runs())

    assert "28 % or more passes" in find_line(lines, "a gate: the share")
    assert "16 V or less passes" in find_line(lines, "the highest the supply reached")


def test_a_membrane_with_no_passing_setup_still_shows_the_closest_one(report, three_runs,
                                                                     monkeypatch):
    """A refusal on its own leaves a reader nowhere, so the nearest setting is printed too."""
    monkeypatch.setattr(config, "RECOVERY_FLOOR_PCT", 99.0)

    lines = report(three_runs())

    assert find_line(lines, "no best setup")
    assert "mA/cm2 at a feed of" in find_line(lines, "closest anyway")
    assert "short of the lithium recovery floor by" in "\n".join(lines)


def test_a_membrane_with_a_passing_setup_shows_no_closest(report, three_runs, monkeypatch):
    """There is nothing to be closest to once a setting passes, so the line would be noise."""
    monkeypatch.setattr(config, "RECOVERY_FLOOR_PCT", 0.0)

    lines = report(three_runs())

    assert find_line(lines, "best setup")
    assert "closest anyway" not in "\n".join(lines)


def test_the_setup_is_also_given_in_the_terms_the_rig_is_set_in(report, three_runs):
    """A supply has milliamps on it, not milliamps per square centimetre."""
    lines = report(three_runs())

    assert "set the supply to" in find_line(lines, "how to run it")
    assert "cm2 membrane" in find_line(lines, "how to run it")


def test_the_feed_is_given_by_weight_as_well_as_by_mole(report, three_runs):
    """A bottle is made up in grammes; the fitting works in moles."""
    lines = report(three_runs())

    assert "g of magnesium for every 1 g of lithium" in "\n".join(lines)


def test_the_feed_in_mg_per_litre_is_given_when_every_run_agrees_on_the_lithium(report,
                                                                               three_runs):
    assert "mg/L of magnesium" in "\n".join(report(three_runs()))


def test_no_feed_in_mg_per_litre_when_the_runs_disagree_on_the_lithium(report, a_run):
    """Quoting one run's lithium as though it were everyone's would mislead."""
    runs = [a_run(run_code="AA", supply_current_a=0.1, li_feed_mg_l=400, mg_feed_mg_l=2430.5),
            a_run(run_code="BB", supply_current_a=0.2, li_feed_mg_l=300, mg_feed_mg_l=3646.0),
            a_run(run_code="CC", supply_current_a=0.4, li_feed_mg_l=400, mg_feed_mg_l=9722.0)]

    assert "mg/L of magnesium" not in "\n".join(report(runs))


def test_the_hours_are_worked_out_on_the_middle_run_not_an_odd_one(report, a_run):
    """One run with a tank four times the size must not drag the figure the report quotes."""
    runs = [a_run(run_code="AA", supply_current_a=0.1, mg_feed_mg_l=2430.5),
            a_run(run_code="BB", supply_current_a=0.2, mg_feed_mg_l=4861.0),
            a_run(run_code="CC", supply_current_a=0.4, mg_feed_mg_l=9722.0)]

    lines = report(runs)

    assert "for a feed tank holding" in find_line(lines, "hours")
    assert "twice as long" in "\n".join(lines)
