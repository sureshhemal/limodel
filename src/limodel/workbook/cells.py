"""Where things sit in a run sheet, and the small helpers that read them.

Both halves of this package — building the CSV files and comparing them back — have to
agree on the layout, so it is described once, here.
"""

SHEET_PREFIX = "New_set"          # the sheets of the Mg/Li set; earlier series are ignored
FIRST_ROW = 9                     # the first row of the time table, below the headers

# Column numbers. The rinse block, below the main table, reuses the concentrate columns.
POWER = {"supply_voltage_v": 3, "supply_current_a": 4, "meter_voltage_v": 5, "meter_current_ma": 6}
CONC = {"id": 13, "conductivity": 14, "ph": 15, "temp": 16, "weight": 17,
        "li": 18, "na": 19, "mg": 20, "k": 21, "ca": 22, "toc": 23}
DIL = {"id": 24, "conductivity": 25, "ph": 26, "temp": 27, "weight": 28,
       "li": 29, "na": 30, "mg": 31, "k": 32, "ca": 33, "toc": 34}
TANKS = {"conc": CONC, "dil": DIL, "rinse": CONC}

MEASURED = ("li", "na", "mg", "k", "ca", "toc")   # what the lab reports for a sample


def run_sheets(book):
    """The Mg/Li run sheets, in workbook order: (run code, sheet)."""
    return [(code_of(name), book[name])
            for name in book.sheetnames if name.startswith(SHEET_PREFIX)]


def code_of(sheet_name):
    """'New_set_Mg2+(07_10_26)_AE' -> 'AE'."""
    return sheet_name.strip().split("_")[-1]


def rinse_row(ws):
    """Row where the rinse block starts, found by the 'Rinse' label in column A."""
    for r in range(FIRST_ROW, ws.max_row + 1):
        if str(ws.cell(r, 1).value).strip().lower() == "rinse":
            return r
    return None


def rinse_rows(ws):
    """minute -> row for the rinse block, which is keyed by the main table's minutes."""
    start = rinse_row(ws)
    if not start:
        return {}

    rows = {}
    for r in range(start, start + 12):
        minute = ws.cell(r, 2).value
        if not isinstance(minute, (int, float)):
            break
        rows[int(minute)] = r
    return rows


def minute_rows(ws):
    """minute -> row for the main table, stopping where the rinse block starts."""
    end = rinse_row(ws) or ws.max_row + 1
    rows = {}
    for r in range(FIRST_ROW, end):
        minute = ws.cell(r, 2).value
        if isinstance(minute, (int, float)):
            rows[int(minute)] = r
    return rows
