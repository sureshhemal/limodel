"""CsvSource reads the four files, keeping the rows the schema takes and naming the rest."""

import pandera.errors
import pytest

from limodel.sources.csv_source import CsvSource


def test_reads_each_file_into_its_own_table(data_dir):
    source = CsvSource(data_dir)

    assert source.runs()["run_code"].tolist() == ["AA", "BB"]
    assert source.stack_readings()["minute"].tolist() == [0, 5, 240, 0, 240]
    assert source.tank_readings()["tank"].tolist() == [
        "conc", "dil", "rinse", "conc", "dil", "conc", "dil", "conc", "dil"]
    assert source.samples()["sample_id"].tolist() == [
        "AA1", "AA2", "AA3", "AA4", "BB1", "BB2", "BB3", "BB4"]


def test_applies_the_types_from_the_schema(data_dir):
    runs = CsvSource(data_dir).runs()

    assert str(runs["run_date"].dtype) == "datetime64[ns]"
    assert str(runs["include"].dtype) == "bool"
    assert str(runs["cell_pairs"].dtype) == "int64"


def test_keeps_a_blank_as_missing_rather_than_zero(data_dir):
    samples = CsvSource(data_dir).samples().set_index("sample_id")

    without_toc = samples.index[samples["toc_ppm"].isna()].tolist()

    assert without_toc == ["AA2", "AA3", "AA4", "BB1", "BB2", "BB3", "BB4"]
    assert samples.loc["AA1", "toc_ppm"] == 0.9749


def test_reads_each_file_only_once(data_dir):
    source = CsvSource(data_dir)
    source.runs()
    (data_dir / "runs.csv").unlink() # deletes the file

    assert source.runs()["run_code"].tolist() == ["AA", "BB"] # still works


def test_says_which_file_is_missing(data_dir):
    (data_dir / "samples.csv").unlink()

    with pytest.raises(FileNotFoundError, match="samples.csv"):
        CsvSource(data_dir).samples()


def test_both_rows_go_when_a_sample_id_is_used_twice(write_file, fixture_text):
    """Neither row can be shown to be the real AA1, so keeping either one would be a guess."""
    data_dir = write_file("samples.csv",
                          fixture_text("samples.csv") + "AA1,BB,5,dil,10,20,,,,,\n")
    source = CsvSource(data_dir)

    kept = source.samples()

    assert "AA1" not in kept["sample_id"].tolist()
    assert [(row.id, row.reason) for row in source.find_refused_rows()] == [
        ("AA1", "sample_id 'AA1' is used more than once"),
        ("AA1", "sample_id 'AA1' is used more than once")]


def test_a_tank_that_is_not_a_tank_is_left_out(write_file, fixture_text):
    data_dir = write_file("tank_readings.csv",
                          fixture_text("tank_readings.csv") + "BB,5,tub,1300,5.9,21,2100,\n")
    source = CsvSource(data_dir)

    kept = source.tank_readings()

    assert "tub" not in kept["tank"].tolist()
    assert source.find_refused_rows()[0].reason == (
        "tank is 'tub', which is not one of the ones allowed")


def test_a_value_outside_its_range_is_left_out(write_file, fixture_text):
    """The other nine readings still load: one bad pH costs its own row and nothing else."""
    data_dir = write_file("tank_readings.csv",
                          fixture_text("tank_readings.csv") + "BB,5,conc,1300,99,21,2100,\n")
    source = CsvSource(data_dir)

    kept = source.tank_readings()

    assert len(kept) == 9
    assert 99 not in kept["ph"].tolist()
    assert "ph is 99" in source.find_refused_rows()[0].reason


def test_a_run_missing_a_required_value_is_left_out_by_name(write_file, fixture_text):
    """The run is named by its code, because a reader has to know which row to go and fix."""
    without_a_membrane = fixture_text("runs.csv").replace("AA,new_set_mg,2026-07-09,GO-10,",
                                                          "AA,new_set_mg,2026-07-09,,")
    data_dir = write_file("runs.csv", without_a_membrane)
    source = CsvSource(data_dir)

    kept = source.runs()

    assert kept["run_code"].tolist() == ["BB"]
    assert [(row.id, row.model, row.reason) for row in source.find_refused_rows()] == [
        ("AA", "Run", "cem is blank")]


def test_a_value_that_is_not_a_number_is_left_out(write_file, fixture_text):
    data_dir = write_file("tank_readings.csv",
                          fixture_text("tank_readings.csv").replace("2119.7", "2168.4.8"))
    source = CsvSource(data_dir)

    source.tank_readings()

    assert "not a number" in source.find_refused_rows()[0].reason


def test_a_file_that_loads_cleanly_refuses_nothing(data_dir):
    source = CsvSource(data_dir)

    source.runs()
    source.tank_readings()

    assert source.find_refused_rows() == ()


def test_rejects_an_unexpected_column(write_file):
    data_dir = write_file("stack_readings.csv",
                          "run_code,minute,supply_voltage_v,supply_current_a,"
                          "meter_voltage_v,meter_current_ma,notes,extra\n"
                          "AA,0,16,0.081,15.93,72.1,,x\n")

    with pytest.raises(pandera.errors.SchemaErrors, match="extra"):
        CsvSource(data_dir).stack_readings()
