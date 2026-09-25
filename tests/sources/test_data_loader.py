"""DataLoader picks its source from the configuration."""

import pytest

from limodel import config
from limodel.data_loader import DataLoader
from limodel.sources.csv_source import CsvSource


def test_uses_the_csv_source_when_configured(monkeypatch, data_dir):
    monkeypatch.setattr(config, "DATA_SOURCE", "csv")
    monkeypatch.setattr(config, "DATA_DIR", data_dir)

    loader = DataLoader()

    assert isinstance(loader.source, CsvSource)
    assert loader.source.data_dir == data_dir


def test_rejects_a_source_it_does_not_know(monkeypatch):
    monkeypatch.setattr(config, "DATA_SOURCE", "mysql")

    with pytest.raises(ValueError, match="is not a source"):
        DataLoader()


def test_hands_out_the_tables_from_its_source(monkeypatch, data_dir):
    monkeypatch.setattr(config, "DATA_SOURCE", "csv")
    monkeypatch.setattr(config, "DATA_DIR", data_dir)

    loader = DataLoader()

    assert loader.runs()["run_code"].tolist() == ["AA", "BB"]
    assert len(loader.stack_readings()) == 3
    assert len(loader.tank_readings()) == 4
    assert loader.samples()["sample_id"].tolist() == ["AA1", "AA2", "BB1"]
