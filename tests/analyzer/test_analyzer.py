"""The Analyzer: which runs the modelling can work from, returned as data."""

import pytest

from limodel import config
from limodel.analyzer import Analyzer, Journal
from limodel.data_loader import DataLoader
from limodel.models import Run


@pytest.fixture
def analyzer(monkeypatch, data_dir):
    monkeypatch.setattr(config, "DATA_SOURCE", "csv")
    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    return Analyzer(DataLoader(), Journal())


def test_uses_every_run_the_lab_has_reported_on(analyzer):
    analysis = analyzer.analyze()

    assert [run.run_code for run in analysis.used] == ["AA", "BB"]
    assert all(isinstance(run, Run) for run in analysis.used)
    assert analysis.waiting == []


def test_sets_aside_a_run_with_no_lab_results(monkeypatch, write_file, fixture_text):
    data_dir = write_file("samples.csv",
                          fixture_text("samples.csv").replace("BB1,BB,0,conc,60,3", "BB1,BB,0,conc,,"))
    monkeypatch.setattr(config, "DATA_SOURCE", "csv")
    monkeypatch.setattr(config, "DATA_DIR", data_dir)

    analysis = Analyzer(DataLoader(), Journal()).analyze()

    assert [run.run_code for run in analysis.used] == ["AA"]
    assert analysis.waiting == ["BB"]


def test_it_fills_the_journal_it_was_given(monkeypatch, write_file, fixture_text):
    data_dir = write_file("runs.csv", fixture_text("runs.csv").replace("42,true,", "42,false,"))
    monkeypatch.setattr(config, "DATA_SOURCE", "csv")
    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    journal = Journal()

    analysis = Analyzer(DataLoader(), journal).analyze()

    assert [run.run_code for run in analysis.used] == ["BB"]
    assert [(left_out.run_code, left_out.reason) for left_out in journal.dropped] == [
        ("AA", "not marked for use")]


def test_prints_nothing(analyzer, capsys):
    analyzer.analyze()

    assert capsys.readouterr().out == ""
