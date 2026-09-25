"""Test data: the small CSV files in tests/fixtures, copied so a test can edit them."""

import shutil
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def data_dir(tmp_path):
    """A copy of the fixture files, in a folder of this test's own."""
    for path in FIXTURES.glob("*.csv"):
        shutil.copy(path, tmp_path / path.name)
    return tmp_path


@pytest.fixture
def fixture_text():
    """The contents of a fixture file, for a test that wants to change something."""
    def read(name):
        return (FIXTURES / name).read_text()
    return read


@pytest.fixture
def write_file(data_dir):
    """Replaces one of the copied files, to test what happens when it is wrong."""
    def write(name, content):
        (data_dir / name).write_text(content)
        return data_dir
    return write
