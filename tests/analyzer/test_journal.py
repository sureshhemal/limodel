"""The Journal: the one record of what the analysis left out."""

from limodel.analyzer.journal import Action, Entry, Journal


class Reading:
    """A stand-in for a model: anything with an id can be written down."""

    def __init__(self, id):
        self.id = id


def test_a_new_journal_is_empty():
    assert Journal().entries == ()


def test_it_keeps_a_dropped_record_with_its_reason():
    journal = Journal()

    journal.drop(Reading("BB"), "not marked for use")

    assert journal.entries == (Entry(Action.DROP, "BB", "Reading", "not marked for use"),)


def test_a_dropped_record_names_no_field():
    journal = Journal()

    journal.drop(Reading("BB"), "not marked for use")

    assert journal.entries[0].field_name == ""


def test_it_keeps_a_skipped_value_with_its_field_and_reason():
    journal = Journal()

    journal.skip(Reading("AJ:conc:0"), "weight_g", "step is more than a tenth of the median")

    assert journal.entries == (Entry(Action.SKIP, "AJ:conc:0", "Reading",
                                     "step is more than a tenth of the median", "weight_g"),)


def test_it_takes_the_model_name_from_the_record():
    journal = Journal()

    journal.drop(Reading("BB"), "not marked for use")

    assert journal.entries[0].model == "Reading"


def test_it_keeps_them_in_the_order_they_happened():
    journal = Journal()

    journal.drop(Reading("BB"), "not marked for use")
    journal.skip(Reading("AA:conc:60"), "ph", "step larger than one unit")
    journal.drop(Reading("AA"), "no lab results yet")

    assert [(str(entry.action), entry.id) for entry in journal.entries] == [
        ("dropped", "BB"), ("skipped", "AA:conc:60"), ("dropped", "AA")]


def test_the_same_record_can_be_written_down_twice():
    journal = Journal()

    journal.skip(Reading("AJ:conc:0"), "weight_g", "step is more than a tenth of the median")
    journal.skip(Reading("AJ:conc:0"), "ph", "step larger than one unit")

    assert [entry.field_name for entry in journal.entries] == ["weight_g", "ph"]


def test_an_action_prints_as_one_word():
    assert f"{Action.DROP}" == "dropped"
    assert f"{Action.SKIP}" == "skipped"


def test_what_it_hands_out_cannot_be_written_to():
    journal = Journal()
    journal.drop(Reading("BB"), "not marked for use")

    entries = journal.entries

    journal.drop(Reading("AA"), "no lab results yet")
    assert len(entries) == 1
