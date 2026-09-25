"""The verify command: compares the data with the workbook it was copied from."""

import pytest
from typer.testing import CliRunner

from limodel import config
from limodel.cli.main import app

runner = CliRunner()


@pytest.fixture
def verify(monkeypatch, workbook, data_dir):
    def run():
        monkeypatch.setattr(config, "WORKBOOK", workbook)
        monkeypatch.setattr(config, "DATA_DIR", data_dir)
        return runner.invoke(app, ["verify"])
    return run


def test_verify_says_so_when_every_value_matches(verify):
    result = verify()

    assert result.exit_code == 0
    assert "across 2 sheets" in result.output
    assert "Every value matches the workbook." in result.output


def test_verify_names_a_value_that_does_not_match(verify, write_file, fixture_text):
    write_file("tank_readings.csv", fixture_text("tank_readings.csv").replace("2119.7", "2119.8"))

    result = verify()

    assert result.exit_code == 0
    assert "1 differences" in result.output
    assert "AA min 0 conc weight_g: csv='2119.8' excel='2119.7'" in result.output


def test_verify_reports_a_reading_the_csv_never_received(verify, write_file, fixture_text):
    write_file("stack_readings.csv",
               "\n".join(line for line in fixture_text("stack_readings.csv").splitlines()
                         if not line.startswith("AA,5")) + "\n")

    result = verify()

    assert result.exit_code == 0
    assert "AA minute 5: power readings in the sheet but missing from stack_readings.csv" \
           in result.output


def test_verify_asks_for_the_workbook_setting(monkeypatch, data_dir):
    monkeypatch.setattr(config, "WORKBOOK", None)
    monkeypatch.setattr(config, "DATA_DIR", data_dir)

    result = runner.invoke(app, ["verify"])

    assert result.exit_code == 1
    assert "Set WORKBOOK in .env" in result.output


def test_verify_says_when_the_workbook_is_not_there(monkeypatch, tmp_path, data_dir):
    monkeypatch.setattr(config, "WORKBOOK", tmp_path / "gone.xlsx")
    monkeypatch.setattr(config, "DATA_DIR", data_dir)

    result = runner.invoke(app, ["verify"])

    assert result.exit_code == 1
    assert "No workbook at" in result.output
