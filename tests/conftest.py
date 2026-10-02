"""Test data: the small CSV files in tests/fixtures, and a workbook holding the same values."""

import shutil
from datetime import datetime
from pathlib import Path

import pytest
from openpyxl import Workbook

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


# Where a value sits in a run sheet: the setup cells, then the columns of a time row.
SETUP = {"B1": datetime(2026, 7, 9), "E1": 400, "E2": 2000, "B3": 2.44, "Q1": "GO-10",
         "Q2": "AR 204", "I1": 0.2, "I2": 6, "M1": 10, "Y2": 96.2, "Y3": 111.5, "Y4": 42,
         "I3": "DI Water +0.5 g/l LiCl", "B5": "2%Wt"}
POWER = 3          # supply voltage, supply current, meter voltage, meter current
CONC = 13          # sample id, conductivity, pH, temperature, weight, Li, Na, Mg, K, Ca, TOC
DIL = 24


def row(ws, r, minute, power, conc=(), dil=()):
    ws.cell(r, 2).value = minute
    for i, value in enumerate(power):
        ws.cell(r, POWER + i).value = value
    for start, block in ((CONC, conc), (DIL, dil)):
        for i, value in enumerate(block):
            ws.cell(r, start + i).value = value


@pytest.fixture
def workbook(tmp_path):
    """A workbook holding exactly what the fixture CSV files hold."""
    book = Workbook()
    book.remove(book.active)

    aa = book.create_sheet("New_set_Mg2+(07_10_26)_AA")
    for cell, value in SETUP.items():
        aa[cell] = value
    row(aa, 9, 0, (16, 0.081, 15.93, 72.1),
        conc=("AA1", 1267.4, 5.845, 21.4, 2119.7, 63.56, None, 2.974, None, None, 0.9749),
        dil=("AA2", 19130.1, 5.889, 21.4, 2117.8, 403.1, None, 1657, None, None, None))
    row(aa, 10, 5, (15.44, 0.082, 15.4, 72.4))
    row(aa, 11, 240, (15.1, 0.081, 15.05, 72.0),
        conc=("AA3", 5095.9, 5.6, 21.6, 2140.2, 210.5, None, 45.2),
        dil=("AA4", 16161.0, 5.7, 21.6, 2090.4, 255.3, None, 1480))
    aa.cell(13, 1).value = "Rinse"
    row(aa, 13, 0, (), conc=(None, 21651.4, 5.04, None, 4074.8))

    bb = book.create_sheet("New_set_Mg2+(07_11_26)_BB")
    for cell, value in SETUP.items():
        bb[cell] = value
    bb["B1"], bb["Q1"], bb["E2"] = datetime(2026, 7, 11), "Pristine", 4000
    bb["Y2"], bb["Y3"], bb["Y4"] = 100, 120, 40
    row(bb, 9, 0, (14, 0.08, 13.9, 71),
        conc=("BB1", 1300, 5.9, 21, 2100, 60, None, 3, None, None, None),
        dil=("BB2", 19000, 5.9, 21, 2110, 400, None, 1650))
    row(bb, 10, 240, (13.5, 0.08, 13.4, 70.5),
        conc=("BB3", 5000, 5.7, 21.2, 2120, 200, None, 40),
        dil=("BB4", 16000, 5.8, 21.2, 2085, 260, None, 1500))

    path = tmp_path / "ED_data.xlsx"
    book.save(path)
    return path
