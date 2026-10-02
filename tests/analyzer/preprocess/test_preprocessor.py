"""Preprocessor: every step, in order, on the runs the one before it returned."""

import pytest

from limodel import config
from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess.preprocessor import Preprocessor
from limodel.analyzer.preprocess.steps.drop_excluded_runs import DropExcludedRuns
from limodel.analyzer.preprocess.steps.drop_runs_missing_an_end_sample import DropRunsMissingAnEndSample
from limodel.analyzer.preprocess.steps.skip_suspect_readings import SkipSuspectReadings
from limodel.analyzer.preprocess.steps.step import Step
from limodel.data_loader import DataLoader


class DropByCode(Step):
    """A stand-in step that drops one named run, to watch the order steps run in."""

    def __init__(self, name, run_code):
        self.name = name
        self.run_code = run_code

    def apply(self, runs, journal):
        return [run for run in runs if run.run_code != self.run_code]


@pytest.fixture
def runs(monkeypatch, data_dir):
    monkeypatch.setattr(config, "DATA_SOURCE", "csv")
    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    return DataLoader().load()


def test_the_steps_in_order():
    assert [type(step) for step in Preprocessor.steps] == [DropExcludedRuns,
                                                           SkipSuspectReadings,
                                                           DropRunsMissingAnEndSample]


def test_run_gives_back_the_runs_the_modelling_can_use(runs):
    assert [run.run_code for run in Preprocessor(Journal()).run(runs)] == ["AA", "BB"]


def test_each_step_gets_the_runs_the_one_before_it_returned(monkeypatch, runs):
    monkeypatch.setattr(Preprocessor, "steps", (DropByCode("first", "AA"), DropByCode("second", "BB")))

    assert Preprocessor(Journal()).run(runs) == []


def test_the_runs_it_is_given_are_not_changed(monkeypatch, runs):
    monkeypatch.setattr(Preprocessor, "steps", (DropByCode("first", "AA"),))
    before = list(runs)

    Preprocessor(Journal()).run(runs)

    assert runs == before


def test_it_writes_down_what_a_step_took_out(monkeypatch, runs):
    monkeypatch.setattr(Preprocessor, "steps", (DropByCode("not marked for use", "BB"),))
    journal = Journal()

    Preprocessor(journal).run(runs)

    assert [(entry.id, entry.model, entry.reason) for entry in journal.entries] == [
        ("BB", "Run", "not marked for use")]


def test_every_step_writes_to_the_same_journal(monkeypatch, runs):
    monkeypatch.setattr(Preprocessor, "steps", (DropByCode("first", "AA"), DropByCode("second", "BB")))
    journal = Journal()

    Preprocessor(journal).run(runs)

    assert [(entry.id, entry.reason) for entry in journal.entries] == [
        ("AA", "first"), ("BB", "second")]


def test_it_writes_nothing_when_no_run_is_taken_out(runs):
    journal = Journal()

    Preprocessor(journal).run(runs)

    assert journal.entries == ()
