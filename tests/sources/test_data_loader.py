"""DataLoader picks its source from configuration and returns runs as objects."""

import pytest

from limodel import config
from limodel.data_loader import DataLoader
from limodel.models import Run, Sample, StackReading, TankReading


@pytest.fixture
def loader(monkeypatch, data_dir):
    monkeypatch.setattr(config, "DATA_SOURCE", "csv")
    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    return DataLoader()


def test_rejects_a_source_it_does_not_know(monkeypatch):
    monkeypatch.setattr(config, "DATA_SOURCE", "mysql")

    with pytest.raises(ValueError, match="is not a source"):
        DataLoader()


def test_loads_one_object_per_run(loader):
    runs = loader.load()

    assert [type(run) for run in runs] == [Run, Run]
    assert [run.run_code for run in runs] == ["AA", "BB"]


def test_a_run_carries_its_own_settings(loader):
    run = loader.load()[0]

    assert run.cem == "GO-10"
    assert run.cell_pairs == 10
    assert run.tare_conc_g == 96.2
    assert run.run_date.isoformat() == "2026-07-09"


def test_a_run_carries_its_readings(loader):
    run = loader.load()[0]

    assert all(isinstance(reading, StackReading) for reading in run.stack_readings)
    assert all(isinstance(reading, TankReading) for reading in run.tank_readings)
    assert [reading.minute for reading in run.stack_readings] == [0, 5]
    assert [reading.id for reading in run.tank_readings] == ["AA:conc:0", "AA:dil:0", "AA:rinse:0"]


def test_a_sample_hangs_off_the_reading_it_was_drawn_from(loader):
    run = loader.load()[0]
    conc = run.tank_readings[0]

    assert isinstance(conc.sample, Sample)
    assert conc.sample.sample_id == "AA1"
    assert conc.sample.li_mg_l == 63.56
    assert conc.sample.tank_id == conc.id


def test_a_reading_with_no_sample_has_none(loader):
    run = loader.load()[0]
    rinse = run.tank_readings[2]

    assert rinse.tank == "rinse"
    assert rinse.sample is None


def test_samples_live_only_on_their_reading(loader):
    run = loader.load()[0]

    assert not hasattr(run, "samples")


def test_the_keys_join_the_objects_up(loader):
    run = loader.load()[0]
    conc = run.tank_readings[0]

    assert run.id == "AA"
    assert conc.run_id == run.id
    assert conc.sample.run_id == run.id
    assert conc.sample.tank_id == conc.id


def test_a_blank_is_missing_rather_than_zero(loader):
    run = loader.load()[0]
    rinse = run.tank_readings[2]

    assert rinse.temp_c is None
    assert run.tank_readings[0].sample.na_mg_l is None
    assert run.mgcl2_6h2o_g_l is None


def test_a_run_whose_rows_have_not_arrived_gets_empty_lists(loader, write_file, fixture_text):
    write_file("tank_readings.csv",
               "\n".join(line for line in fixture_text("tank_readings.csv").splitlines()
                         if not line.startswith("BB")) + "\n")

    runs = {run.run_code: run for run in DataLoader().load()}

    assert runs["BB"].tank_readings == []
    assert runs["AA"].tank_readings != []
