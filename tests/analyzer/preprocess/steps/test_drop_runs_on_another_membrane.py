"""DropRunsOnAnotherMembrane: only the runs made on the membranes being modelled."""

import pytest

from limodel import config
from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess.steps.drop_runs_on_another_membrane import DropRunsOnAnotherMembrane


@pytest.fixture
def journal():
    return Journal()


def test_it_says_what_it_takes_out():
    assert DropRunsOnAnotherMembrane().name == "not a membrane being modelled"


def test_it_takes_the_membranes_from_the_settings_when_given_none(monkeypatch):
    monkeypatch.setattr(config, "MEMBRANES_MODELLED", ("GO-10",))

    assert DropRunsOnAnotherMembrane().find_membranes() == ("GO-10",)


def test_what_it_is_given_beats_the_settings(monkeypatch):
    monkeypatch.setattr(config, "MEMBRANES_MODELLED", ("GO-10",))

    assert DropRunsOnAnotherMembrane("Pristine").find_membranes() == ("Pristine",)


def test_one_membrane_may_be_given_on_its_own():
    assert DropRunsOnAnotherMembrane("Pristine").find_membranes() == ("Pristine",)


def test_several_membranes_may_be_given_together():
    assert DropRunsOnAnotherMembrane(["GO-10", "Pristine"]).find_membranes() == ("GO-10", "Pristine")


def test_the_settings_may_name_several_too(monkeypatch):
    monkeypatch.setattr(config, "MEMBRANES_MODELLED", ("GO-10", "Pristine"))

    assert DropRunsOnAnotherMembrane().find_membranes() == ("GO-10", "Pristine")


def test_a_run_on_the_membrane_being_modelled_is_kept(a_run, journal):
    given = [a_run(run_code="AE", cem="GO-10")]

    assert DropRunsOnAnotherMembrane("GO-10").apply(given, journal) == given


def test_a_run_on_another_membrane_is_taken_out(a_run, journal):
    wanted = a_run(run_code="AE", cem="GO-10")
    other = a_run(run_code="AK", cem="Pristine")

    kept = DropRunsOnAnotherMembrane("GO-10").apply([wanted, other], journal)

    assert [run.run_code for run in kept] == ["AE"]


def test_every_named_membrane_is_kept(a_run, journal):
    runs = [a_run(run_code="AE", cem="GO-10"),
            a_run(run_code="AK", cem="Pristine"),
            a_run(run_code="AR", cem="PDA/PEI/15CE/BT")]

    kept = DropRunsOnAnotherMembrane(("GO-10", "Pristine")).apply(runs, journal)

    assert [run.run_code for run in kept] == ["AE", "AK"]


def test_the_runs_keep_the_order_they_came_in(a_run, journal):
    runs = [a_run(run_code=code, cem="GO-10") for code in ("AT", "AE", "AN")]

    kept = DropRunsOnAnotherMembrane("GO-10").apply(runs, journal)

    assert [run.run_code for run in kept] == ["AT", "AE", "AN"]


def test_a_membrane_written_another_way_is_still_that_membrane(a_run, journal):
    """AW is written GO10 in the workbook; the model tidies it, so this step sees GO-10."""
    runs = [a_run(run_code="AE", cem="GO-10"), a_run(run_code="AW", cem="GO10")]

    kept = DropRunsOnAnotherMembrane("GO-10").apply(runs, journal)

    assert [run.run_code for run in kept] == ["AE", "AW"]


def test_a_membrane_no_run_was_made_on_is_an_error(a_run, journal):
    runs = [a_run(run_code="AE", cem="GO-10")]

    with pytest.raises(ValueError, match="no run is left"):
        DropRunsOnAnotherMembrane("GO-20").apply(runs, journal)


def test_no_runs_at_all_is_not_an_error(journal):
    assert DropRunsOnAnotherMembrane("GO-10").apply([], journal) == []


def test_it_writes_nothing_itself(a_run, journal):
    """The preprocessor writes the journal entry, so a step only chooses."""
    runs = [a_run(run_code="AE", cem="GO-10"), a_run(run_code="AK", cem="Pristine")]

    DropRunsOnAnotherMembrane("GO-10").apply(runs, journal)

    assert journal.entries == ()
