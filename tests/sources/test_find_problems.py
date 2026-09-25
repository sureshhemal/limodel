"""find_problems reports what is wrong with the data instead of raising."""

import pandas as pd

from limodel.checks import find_problems
from limodel.sources.csv_source import CsvSource


def problems_in(data_dir):
    return find_problems(CsvSource(data_dir).raw_tables())


def test_finds_nothing_wrong_with_good_data(data_dir):
    assert problems_in(data_dir) == []


def test_reports_a_missing_file(data_dir):
    (data_dir / "samples.csv").unlink()

    problems = problems_in(data_dir)

    assert [(p.table, p.problem) for p in problems] == [("samples", "file is missing")]


def test_reports_a_value_that_is_not_a_number(write_file, fixture_text):
    data_dir = write_file("tank_readings.csv",
                          fixture_text("tank_readings.csv").replace("2119.7", "2168.4.8"))

    problems = problems_in(data_dir)

    assert len(problems) == 1
    assert problems[0].table == "tank_readings"
    assert problems[0].where == "AA minute 0 conc"
    assert problems[0].column == "weight_g"
    assert problems[0].value == "2168.4.8"
    assert problems[0].problem == "not a number"


def test_reports_both_rows_that_share_a_sample_id(write_file, fixture_text):
    data_dir = write_file("samples.csv",
                          fixture_text("samples.csv") + "AA1,BB,5,dil,10,20,,,,,\n")

    problems = problems_in(data_dir)

    assert [p.where for p in problems] == ["AA minute 0 conc AA1", "BB minute 5 dil AA1"]
    assert {p.problem for p in problems} == {"used more than once"}


def test_reports_a_required_value_that_is_missing(write_file, fixture_text):
    without_a_membrane = fixture_text("runs.csv").replace("AA,new_set_mg,2026-07-09,GO-10,",
                                                          "AA,new_set_mg,2026-07-09,,")
    data_dir = write_file("runs.csv", without_a_membrane)

    problems = problems_in(data_dir)

    assert [(p.column, p.problem) for p in problems] == [("cem", "required, but blank")]


def test_reports_a_value_outside_its_range(write_file, fixture_text):
    data_dir = write_file("tank_readings.csv",
                          fixture_text("tank_readings.csv") + "BB,5,conc,1300,99,21,2100,\n")

    problems = problems_in(data_dir)

    assert [(p.column, p.value) for p in problems] == [("ph", "99.0")]
    assert "outside its range" in problems[0].problem


def test_reports_a_tank_that_is_not_a_tank(write_file, fixture_text):
    data_dir = write_file("tank_readings.csv",
                          fixture_text("tank_readings.csv") + "BB,5,tub,1300,5.9,21,2100,\n")

    problems = problems_in(data_dir)

    assert [(p.column, p.value) for p in problems] == [("tank", "tub")]
    assert "not one of" in problems[0].problem


def test_reports_an_unexpected_column(write_file):
    data_dir = write_file("stack_readings.csv",
                          "run_code,minute,supply_voltage_v,supply_current_a,"
                          "meter_voltage_v,meter_current_ma,notes,extra\n"
                          "AA,0,16,0.081,15.93,72.1,,x\n")

    problems = problems_in(data_dir)

    assert [(p.value, p.problem) for p in problems] == [("extra", "unexpected column")]


def test_reports_every_table_in_one_go(write_file, fixture_text):
    write_file("runs.csv", fixture_text("runs.csv").replace("GO-10", ""))
    data_dir = write_file("tank_readings.csv",
                          fixture_text("tank_readings.csv").replace("2119.7", "2168.4.8"))

    tables = {name: table for name, table in CsvSource(data_dir).raw_tables().items()}

    assert {p.table for p in find_problems(tables)} == {"runs", "tank_readings"}


def test_says_nothing_about_a_table_it_cannot_read(data_dir):
    tables = CsvSource(data_dir).raw_tables()
    tables["samples"] = pd.DataFrame()

    problems = find_problems(tables)

    assert {p.table for p in problems} == {"samples"}
