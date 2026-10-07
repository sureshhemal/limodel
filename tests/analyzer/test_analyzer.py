"""The Analyzer: which runs the modelling can work from, returned as data."""

import pytest

from limodel import config
from limodel.analyzer import Analyzer, Journal, Result
from limodel.data_loader import DataLoader
from limodel.models import Run


@pytest.fixture
def analyzer(monkeypatch, data_dir):
    monkeypatch.setattr(config, "DATA_SOURCE", "csv")
    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    return Analyzer(DataLoader(), Journal())


def test_uses_every_run_the_lab_has_answered_for(analyzer):
    analysis = analyzer.analyze()

    assert [run.run_code for run in analysis.used] == ["AA", "BB"]
    assert all(isinstance(run, Run) for run in analysis.used)


def test_sets_aside_a_run_the_lab_has_not_finished_with(monkeypatch, write_file, fixture_text):
    data_dir = write_file("samples.csv",
                          fixture_text("samples.csv").replace("BB1,BB,0,conc,60,3", "BB1,BB,0,conc,,"))
    monkeypatch.setattr(config, "DATA_SOURCE", "csv")
    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    journal = Journal()

    analysis = Analyzer(DataLoader(), journal).analyze()

    assert [run.run_code for run in analysis.used] == ["AA"]
    assert [(entry.id, entry.reason) for entry in journal.entries] == [
        ("BB", "no lab results at both ends")]


def test_it_fills_the_journal_it_was_given(monkeypatch, write_file, fixture_text):
    data_dir = write_file("runs.csv", fixture_text("runs.csv").replace("42,true,", "42,false,"))
    monkeypatch.setattr(config, "DATA_SOURCE", "csv")
    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    journal = Journal()

    analysis = Analyzer(DataLoader(), journal).analyze()

    assert [run.run_code for run in analysis.used] == ["BB"]
    assert [(entry.id, entry.model, entry.reason) for entry in journal.entries] == [
        ("AA", "Run", "not marked for use")]


def test_every_run_it_uses_gets_a_result_beside_it(analyzer):
    analysis = analyzer.analyze()

    assert [result.run_code for result in analysis.results] == ["AA", "BB"]
    assert all(isinstance(result, Result) for result in analysis.results)


def test_sets_aside_a_run_whose_numbers_will_not_come_out(monkeypatch, write_file,
                                                          fixture_text):
    """A feed reported with no lithium in it leaves recovery nothing to measure against."""
    data_dir = write_file("samples.csv", fixture_text("samples.csv").replace(
        "AA2,AA,0,dil,403.1,1657", "AA2,AA,0,dil,0,1657"))
    monkeypatch.setattr(config, "DATA_SOURCE", "csv")
    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    journal = Journal()

    analysis = Analyzer(DataLoader(), journal).analyze()

    assert [run.run_code for run in analysis.used] == ["AA", "BB"]
    assert [result.run_code for result in analysis.results] == ["BB"]
    assert [(entry.id, entry.reason) for entry in journal.entries] == [
        ("AA", "permselectivity and lithium recovery could not be worked out")]


def test_prints_nothing(analyzer, capsys):
    analyzer.analyze()

    assert capsys.readouterr().out == ""
