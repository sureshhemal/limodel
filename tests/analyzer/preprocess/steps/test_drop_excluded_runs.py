"""DropExcludedRuns: only the runs marked for use go on, and nothing else changes."""

import pytest

from limodel import config
from limodel.analyzer.preprocess.steps.drop_excluded_runs import DropExcludedRuns
from limodel.data_loader import DataLoader


@pytest.fixture
def runs(monkeypatch, data_dir):
    """The fixture runs as objects, optionally loaded from a folder of their own."""
    def load(into=data_dir):
        monkeypatch.setattr(config, "DATA_SOURCE", "csv")
        monkeypatch.setattr(config, "DATA_DIR", into)
        return DataLoader().load()
    return load


@pytest.fixture
def marked_not_to_be_used(write_file, fixture_text):
    """The same runs.csv, with the named runs marked not to be used."""
    def mark(*run_codes):
        marked = tuple(f"{run_code}," for run_code in run_codes)
        return write_file("runs.csv", "\n".join(
            row[: row.rindex("true,")] + "false," if row.startswith(marked) else row
            for row in fixture_text("runs.csv").splitlines()) + "\n")
    return mark


def test_every_run_marked_for_use_is_kept_in_order(runs):
    result = DropExcludedRuns().apply(runs())

    assert [run.run_code for run in result] == ["AA", "BB"]


def test_a_run_marked_not_to_be_used_is_dropped(runs, marked_not_to_be_used):
    result = DropExcludedRuns().apply(runs(into=marked_not_to_be_used("BB")))

    assert [run.run_code for run in result] == ["AA"]


def test_the_runs_it_keeps_are_the_objects_it_was_given(runs):
    given = runs()

    result = DropExcludedRuns().apply(given)

    assert result[0] is given[0]


def test_the_list_it_is_given_is_not_changed(runs, marked_not_to_be_used):
    given = runs(into=marked_not_to_be_used("BB"))
    before = list(given)

    DropExcludedRuns().apply(given)

    assert given == before


def test_it_stops_when_no_run_is_marked_for_use(runs, marked_not_to_be_used):
    with pytest.raises(ValueError, match="no run is left: all 2"):
        DropExcludedRuns().apply(runs(into=marked_not_to_be_used("AA", "BB")))


def test_no_runs_at_all_is_not_an_error(runs):
    assert DropExcludedRuns().apply([]) == []
