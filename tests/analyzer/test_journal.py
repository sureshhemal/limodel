"""The Journal: the one record of what the analysis left out."""

from limodel.analyzer.journal import Dropped, Journal


def test_a_new_journal_is_empty():
    assert Journal().dropped == ()


def test_it_keeps_a_dropped_run_with_its_reason():
    journal = Journal()

    journal.drop("BB", "not marked for use")

    assert journal.dropped == (Dropped("BB", "not marked for use"),)


def test_it_keeps_them_in_the_order_they_were_dropped():
    journal = Journal()

    journal.drop("BB", "not marked for use")
    journal.drop("AA", "no lab results yet")

    assert [left_out.run_code for left_out in journal.dropped] == ["BB", "AA"]


def test_the_same_run_can_be_dropped_for_a_second_reason():
    journal = Journal()

    journal.drop("BB", "not marked for use")
    journal.drop("BB", "missing a setting")

    assert [left_out.reason for left_out in journal.dropped] == ["not marked for use",
                                                                "missing a setting"]


def test_what_it_hands_out_cannot_be_written_to():
    journal = Journal()
    journal.drop("BB", "not marked for use")

    dropped = journal.dropped

    journal.drop("AA", "no lab results yet")
    assert len(dropped) == 1
