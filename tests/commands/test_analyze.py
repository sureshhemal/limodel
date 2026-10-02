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
    assert "using 2 runs, 2 with lab results" in result.output
    assert "skipped" not in result.output


def test_analyze_names_the_runs_still_waiting_for_the_lab(analyze, write_file, fixture_text):
    data_dir = write_file("samples.csv", fixture_text("samples.csv").replace("BB1,BB,0,conc,60,3",
                                                                            "BB1,BB,0,conc,,"))

    result = analyze(into=data_dir)

    assert result.exit_code == 0
    assert "using 2 runs, 1 with lab results" in result.output
    assert "waiting  BB   no lab results yet" in result.output


def test_analyze_leaves_out_a_run_marked_not_to_be_used(analyze, write_file, fixture_text):
    data_dir = write_file("runs.csv", fixture_text("runs.csv").replace("42,true,", "42,false,"))

    result = analyze(into=data_dir)

    assert result.exit_code == 0
    assert "dropped  AA   not marked for use" in result.output
    assert "using 1 runs, 1 with lab results" in result.output
