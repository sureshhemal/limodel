"""The check command: lists what is wrong with the data, and never fails."""

from typer.testing import CliRunner

from limodel import config
from limodel.cli.main import app

runner = CliRunner()


def run_check(monkeypatch, data_dir):
    monkeypatch.setattr(config, "DATA_SOURCE", "csv")
    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    return runner.invoke(app, ["check"])


def test_check_says_so_when_the_data_is_good(monkeypatch, data_dir):
    result = run_check(monkeypatch, data_dir)

    assert result.exit_code == 0
    assert "No problems found." in result.output


def test_check_lists_what_is_wrong(monkeypatch, write_file, fixture_text):
    data_dir = write_file("tank_readings.csv",
                          fixture_text("tank_readings.csv").replace("2119.7", "2168.4.8"))

    result = run_check(monkeypatch, data_dir)

    assert result.exit_code == 0
    assert "1 problems found" in result.output
    assert "AA minute 0 conc" in result.output
    assert "weight_g" in result.output
    assert "2168.4.8" in result.output
    assert "not a number" in result.output


def test_check_does_not_fail_when_a_file_is_missing(monkeypatch, data_dir):
    (data_dir / "runs.csv").unlink()

    result = run_check(monkeypatch, data_dir)

    assert result.exit_code == 0
    assert "file is missing" in result.output
