"""The analyze command: says what the modelling can use before it models anything."""

import pytest
from typer.testing import CliRunner

from limodel import config
from limodel.cli.main import app

runner = CliRunner()


@pytest.fixture
def analyze(monkeypatch, data_dir):
    def run(into=data_dir):
        monkeypatch.setattr(config, "DATA_SOURCE", "csv")
        monkeypatch.setattr(config, "DATA_DIR", into)
        return runner.invoke(app, ["analyze"])
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
