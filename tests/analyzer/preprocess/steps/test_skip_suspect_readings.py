"""SkipSuspectReadings: each tank is judged on its own series, and a value it cannot
believe is taken out and written down."""

import pytest

from limodel import config
from limodel.analyzer.journal import Action, Journal
from limodel.analyzer.preprocess.steps.skip_suspect_readings import SkipSuspectReadings
from limodel.analyzer.thresholds import Thresholds
from limodel.data_loader import DataLoader

HEADER = "run_code,minute,tank,conductivity_us_cm,ph,temp_c,weight_g,notes"

# three weights per tank, at minutes 0, 5 and 10. A tenth of the concentrate's median is
# some 212 g and a tenth of the rinse's some 407 g, so each tank is judged at its own scale.
CONC = (2119.7, 2117.8, 2100.0)
DIL = (2117.8, 2110.0, 2090.0)
RINSE = (4074.8, 4070.0, 4060.0)

CONC_JUMPED = (2119.7, 2117.8, 1800.0)
DIL_JUMPED = (2117.8, 2110.0, 1800.0)
RINSE_JUMPED = (4074.8, 4070.0, 3500.0)


@pytest.fixture
def runs(monkeypatch, write_file):
    """The runs, with any tank's weights replaced by the ones a test wants to try."""
    def load(**weights_by_tank):
        series = {"conc": CONC, "dil": DIL, "rinse": RINSE} | weights_by_tank
        rows = [f"AA,{reading * 5},{tank},1267.4,5.845,21.4,{weight},"
                for tank, weights in series.items()
                for reading, weight in enumerate(weights)]
        monkeypatch.setattr(config, "DATA_SOURCE", "csv")
        monkeypatch.setattr(config, "DATA_DIR",
                            write_file("tank_readings.csv", "\n".join([HEADER, *rows]) + "\n"))
        return DataLoader().load()
    return load


def weights_of(runs, tank):
    """What one tank's readings hold, in minute order."""
    return [reading.weight_g for run in runs
            for reading in sorted(run.tank_readings, key=lambda reading: reading.minute)
            if reading.tank == tank]


def test_believable_weights_are_left_alone(runs):
    given = runs()
    journal = Journal()

    SkipSuspectReadings().apply(given, journal)

    assert weights_of(given, "conc") == list(CONC)
    assert weights_of(given, "dil") == list(DIL)
    assert weights_of(given, "rinse") == list(RINSE)
    assert journal.entries == ()


def test_every_run_is_passed_on(runs):
    given = runs(conc=CONC_JUMPED)

    result = SkipSuspectReadings().apply(given, Journal())

    assert [run.run_code for run in result] == [run.run_code for run in given]


def test_a_weight_the_concentrate_cannot_have_reached_is_taken_out(runs):
    given = runs(conc=CONC_JUMPED)

    SkipSuspectReadings().apply(given, Journal())

    assert weights_of(given, "conc") == [2119.7, 2117.8, None]


def test_the_diluate_is_checked_too(runs):
    given = runs(dil=DIL_JUMPED)

    SkipSuspectReadings().apply(given, Journal())

    assert weights_of(given, "dil") == [2117.8, 2110.0, None]


def test_the_rinse_is_checked_too(runs):
    given = runs(rinse=RINSE_JUMPED)

    SkipSuspectReadings().apply(given, Journal())

    assert weights_of(given, "rinse") == [4074.8, 4070.0, None]


def test_one_bad_tank_leaves_the_others_alone(runs):
    given = runs(dil=DIL_JUMPED)

    SkipSuspectReadings().apply(given, Journal())

    assert weights_of(given, "conc") == list(CONC)
    assert weights_of(given, "rinse") == list(RINSE)


def test_each_tank_is_judged_at_its_own_scale(runs):
    """570 g is impossible in the concentrate and believable nowhere else, so the rinse,
    which is twice the weight, must be judged by its own median rather than another tank's."""
    given = runs(rinse=(4074.8, 4070.0, 3700.0))

    SkipSuspectReadings().apply(given, Journal())

    assert weights_of(given, "rinse") == [4074.8, 4070.0, 3700.0]


def test_the_reading_keeps_everything_else(runs):
    given = runs(conc=CONC_JUMPED)

    SkipSuspectReadings().apply(given, Journal())

    reading = next(r for run in given for r in run.tank_readings
                   if r.tank == "conc" and r.minute == 10)
    assert (reading.conductivity_us_cm, reading.ph, reading.temp_c) == (1267.4, 5.845, 21.4)


def test_the_skip_is_written_down_with_its_field_and_reason(runs):
    journal = Journal()

    SkipSuspectReadings().apply(runs(conc=CONC_JUMPED), journal)

    entry = journal.entries[0]
    assert (entry.action, entry.id, entry.model, entry.field_name) == (
        Action.SKIP, "AA:conc:10", "TankReading", "weight_g")
    assert entry.reason == "weight 1800 g is 317.8 g away from the usual 2117.8 g"


def test_a_series_of_one_weight_is_left_alone(runs):
    journal = Journal()

    SkipSuspectReadings().apply(runs(conc=(2119.7,)), journal)

    assert journal.entries == ()


def test_the_threshold_it_is_given_decides(runs):
    journal = Journal()

    SkipSuspectReadings(Thresholds(impossible_weight_share=0.0001)).apply(runs(), journal)

    assert [entry.id for entry in journal.entries] == [
        "AA:conc:10", "AA:dil:10", "AA:rinse:10"]


def test_a_bad_first_reading_is_the_one_taken_out(runs):
    """The empty-tank reading at the start of a run. Judged against its neighbour the good
    second reading would be blamed; judged against the median it is the stranger."""
    given = runs(conc=(209.7, 2098.9, 2088.9, 2079.5))

    SkipSuspectReadings().apply(given, Journal())

    assert weights_of(given, "conc") == [None, 2098.9, 2088.9, 2079.5]


def test_a_typo_in_the_middle_does_not_take_its_neighbour_with_it(runs):
    given = runs(conc=(2119.7, 2117.8, 209.7, 2100.0, 2098.5))
    journal = Journal()

    SkipSuspectReadings().apply(given, journal)

    assert weights_of(given, "conc") == [2119.7, 2117.8, None, 2100.0, 2098.5]
    assert [entry.id for entry in journal.entries] == ["AA:conc:10"]


def test_one_entry_per_value_taken_out(runs):
    journal = Journal()

    SkipSuspectReadings().apply(runs(conc=(2119.7, 2117.8, 209.7, 2100.0, 2098.5)), journal)

    assert len(journal.entries) == 1


def test_a_series_of_two_weights_cannot_be_judged(runs):
    """Their median is their midpoint, so each sits exactly as far from it as the other."""
    journal = Journal()

    SkipSuspectReadings().apply(runs(conc=(209.7, 2098.9)), journal)

    assert journal.entries == ()


def test_it_stops_rather_than_emptying_a_series_it_cannot_mend(runs):
    given = runs(conc=(2100.0, 2098.0, 10.0, 12.0, 11.0, 2099.0, 2097.0, 2096.0))
    journal = Journal()

    SkipSuspectReadings().apply(given, journal)

    assert len(journal.entries) == 2
    assert weights_of(given, "conc").count(None) == 2


@pytest.fixture
def ph_series(monkeypatch, write_file):
    """One tank whose pH readings, and the minutes they were taken at, a test chooses."""
    def load(values, minutes=(0, 15, 30)):
        rows = [f"AA,{minute},conc,1267.4,{ph},21.4,2100.0,"
                for minute, ph in zip(minutes, values)]
        monkeypatch.setattr(config, "DATA_SOURCE", "csv")
        monkeypatch.setattr(config, "DATA_DIR",
                            write_file("tank_readings.csv", "\n".join([HEADER, *rows]) + "\n"))
        return DataLoader().load()
    return load


def ph_of(runs):
    """The concentrate's pH readings, in minute order."""
    return [reading.ph for run in runs
            for reading in sorted(run.tank_readings, key=lambda reading: reading.minute)]


def test_ph_that_moves_slowly_is_left_alone(ph_series):
    given = ph_series((5.9, 5.85, 5.8))
    journal = Journal()

    SkipSuspectReadings().apply(given, journal)

    assert ph_of(given) == [5.9, 5.85, 5.8]
    assert journal.entries == ()


def test_a_change_inside_the_allowance_is_left_alone(ph_series):
    """1.0 in 15 minutes is under the 1.5 allowed."""
    given = ph_series((5.9, 4.9, 4.85))

    SkipSuspectReadings().apply(given, Journal())

    assert ph_of(given) == [5.9, 4.9, 4.85]


def test_ph_moving_too_fast_loses_the_reading_further_from_the_usual(ph_series):
    given = ph_series((5.9, 4.1, 5.85))
    journal = Journal()

    SkipSuspectReadings().apply(given, journal)

    assert ph_of(given) == [5.9, None, 5.85]
    assert journal.entries[0].field_name == "ph"
    assert journal.entries[0].reason == "pH moved 1.8 in 15 minutes, more than 1.5 in 15"


def test_the_same_change_over_longer_is_allowed(ph_series):
    """1.8 is too fast across 15 minutes and ordinary drift across 240."""
    given = ph_series((5.9, 4.1, 4.05), minutes=(0, 240, 480))

    SkipSuspectReadings().apply(given, Journal())

    assert ph_of(given) == [5.9, 4.1, 4.05]


def test_a_bad_first_reading_is_the_one_lost(ph_series):
    given = ph_series((4.0, 5.9, 5.95))

    SkipSuspectReadings().apply(given, Journal())

    assert ph_of(given) == [None, 5.9, 5.95]


def test_a_ph_outside_the_range_goes_however_slowly_it_got_there(ph_series):
    given = ph_series((0.072, 0.08, 0.09), minutes=(0, 240, 480))
    journal = Journal()

    SkipSuspectReadings().apply(given, journal)

    assert journal.entries[0].reason == "pH 0.072 is outside 2 to 12"


def test_the_weights_are_not_touched_by_the_ph_check(ph_series):
    given = ph_series((5.9, 4.1, 5.85))

    SkipSuspectReadings().apply(given, Journal())

    assert weights_of(given, "conc") == [2100.0, 2100.0, 2100.0]
