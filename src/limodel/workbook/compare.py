"""Compares the CSV files with her workbook: every value must match the cell it came from."""

import csv
import re
from dataclasses import dataclass

import openpyxl

from limodel.workbook.cells import (MEASURED, POWER, TANKS, minute_rows, rinse_rows,
                                    run_sheets)

# Which column of a CSV file comes from which key of the sheet's tank block.
TANK_MEASURES = {"conductivity_us_cm": "conductivity", "ph": "ph",
                 "temp_c": "temp", "weight_g": "weight"}
SAMPLE_MEASURES = {"li_mg_l": "li", "mg_mg_l": "mg", "na_mg_l": "na",
                   "k_mg_l": "k", "ca_mg_l": "ca", "toc_ppm": "toc"}

RUN_CELLS = [("run_date", 1, 2), ("li_feed_mg_l", 1, 5), ("mg_feed_mg_l", 2, 5),
             ("licl_g_l", 3, 2), ("mgcl2_6h2o_g_l", 2, 2), ("cem", 1, 17), ("aem", 2, 17),
             ("flow_l_min", 1, 9), ("area_cm2", 2, 9), ("cell_pairs", 1, 13),
             ("tare_conc_g", 2, 25), ("tare_dil_g", 3, 25), ("tare_rinse_g", 4, 25)]


def _norm(value):
    """Excel value as the string a faithful CSV would hold."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _same(csv_value, excel_value):
    written, expected = csv_value.strip(), _norm(excel_value)
    if written == expected:
        return True
    try:
        return abs(float(written) - float(expected)) < 1e-12
    except (ValueError, TypeError):
        return False


def _read_rows(path):
    return list(csv.DictReader(open(path)))


def _orphan_values(ws, row, cols):
    """Lab values in a sheet row that carries no sample ID."""
    if _norm(ws.cell(row, cols["id"]).value):
        return []
    return [f"{m}={_norm(ws.cell(row, cols[m]).value)}"
            for m in MEASURED if _norm(ws.cell(row, cols[m]).value)]


def _index_sheets(book):
    """code -> (sheet, {minute: row}, {(minute, tank): row})."""
    sheets = {}
    for code, ws in run_sheets(book):
        rinse = rinse_rows(ws)
        stack_rows = minute_rows(ws)

        tank_rows = {}
        for minute, r in stack_rows.items():
            tank_rows[(minute, "conc")] = r
            tank_rows[(minute, "dil")] = r
        for minute, r in rinse.items():
            tank_rows[(minute, "rinse")] = r

        sheets[code] = (ws, stack_rows, tank_rows)
    return sheets


def _compare_runs(sheets, path, differences):
    checked = 0
    in_csv = set()
    for row in _read_rows(path):
        in_csv.add(row["run_code"])
        ws = sheets[row["run_code"]][0]
        for field, r, c in RUN_CELLS:
            checked += 1
            value = ws.cell(r, c).value
            if field == "run_date" and hasattr(value, "date"):
                matches = row[field] == value.date().isoformat()
            else:
                matches = _same(row[field], value)
            if not matches:
                differences.append(f"{row['run_code']} run {field}: "
                                   f"csv={row[field]!r} excel={_norm(value)!r}")
        checked += 2
        text = _norm(ws.cell(3, 9).value)
        match = re.search(r"([\d.]+)\s*g/?l\s*([A-Za-z0-9]+)", text, re.I)
        if match:
            amount, salt = match.groups()
            if row["conc_start_salt"] != salt or float(row["conc_start_g_l"]) != float(amount):
                differences.append(f"{row['run_code']} run conc_start: "
                                   f"csv={row['conc_start_salt']!r},{row['conc_start_g_l']} "
                                   f"sheet text={text!r}")
        rinse_text = _norm(ws.cell(5, 2).value)
        number = re.search(r"[\d.]+", rinse_text)
        if number and float(row["rinse_wt_pct"]) != float(number.group()):
            differences.append(f"{row['run_code']} run rinse_wt_pct: "
                               f"csv={row['rinse_wt_pct']} sheet text={rinse_text!r}")
    for code in sheets:
        if code not in in_csv:
            differences.append(f"{code}: sheet exists but has no row in runs.csv")
    return checked


def _compare_stack(sheets, path, differences):
    checked = 0
    seen = set()
    for row in _read_rows(path):
        code, minute = row["run_code"], int(row["minute"])
        ws, stack_rows, _ = sheets[code]
        if minute not in stack_rows:
            differences.append(f"{code} minute {minute}: no such row in the sheet")
            continue
        seen.add((code, minute))
        r = stack_rows[minute]
        for field, column in POWER.items():
            checked += 1
            if not _same(row[field], ws.cell(r, column).value):
                differences.append(f"{code} min {minute} {field}: "
                                   f"csv={row[field]!r} excel={_norm(ws.cell(r, column).value)!r}")

    for code, (ws, stack_rows, _) in sheets.items():
        for minute, r in stack_rows.items():
            has_power = any(ws.cell(r, c).value is not None for c in POWER.values())
            if has_power and (code, minute) not in seen:
                differences.append(f"{code} minute {minute}: power readings in the sheet but "
                                   f"missing from stack_readings.csv")
    return checked


def _compare_tanks(sheets, path, differences):
    checked = 0
    seen = set()
    for row in _read_rows(path):
        code, minute, tank = row["run_code"], int(row["minute"]), row["tank"]
        ws, _, tank_rows = sheets[code]
        r = tank_rows.get((minute, tank))
        if r is None:
            differences.append(f"{code} minute {minute} {tank}: no such row in the sheet")
            continue
        seen.add((code, minute, tank))
        cols = TANKS[tank]
        for field, key in TANK_MEASURES.items():
            checked += 1
            cell = ws.cell(r, cols[key]).value
            if not _same(row[field], cell):
                differences.append(f"{code} min {minute} {tank} {field}: "
                                   f"csv={row[field]!r} excel={_norm(cell)!r}")
        # lab values with no sample ID are kept here, in notes
        for value in _orphan_values(ws, r, cols):
            checked += 1
            if value not in row["notes"]:
                differences.append(f"{code} minute {minute} {tank}: sheet has {value} with no "
                                   f"sample ID, and it is not recorded in the CSV")

    for code, (ws, _, tank_rows) in sheets.items():
        for (minute, tank), r in tank_rows.items():
            cols = TANKS[tank]
            has_value = any(ws.cell(r, cols[k]).value is not None for k in TANK_MEASURES.values())
            if (has_value or _orphan_values(ws, r, cols)) and (code, minute, tank) not in seen:
                differences.append(f"{code} minute {minute} {tank}: values in the sheet but "
                                   f"missing from tank_readings.csv")
    return checked


def _compare_samples(sheets, path, differences):
    checked = 0
    seen = set()
    for row in _read_rows(path):
        code, minute, tank = row["run_code"], int(row["minute"]), row["tank"]
        ws, _, tank_rows = sheets[code]
        r = tank_rows.get((minute, tank))
        if r is None:
            differences.append(f"{code} {row['sample_id']}: no row in the sheet at "
                               f"minute {minute} {tank}")
            continue
        seen.add((code, minute, tank))
        cols = TANKS[tank]
        checked += 1
        if row["sample_id"] != _norm(ws.cell(r, cols["id"]).value):
            differences.append(f"{code} min {minute} {tank} sample_id: csv={row['sample_id']!r} "
                               f"excel={_norm(ws.cell(r, cols['id']).value)!r}")
        for field, key in SAMPLE_MEASURES.items():
            checked += 1
            cell = ws.cell(r, cols[key]).value
            if not _same(row[field], cell):
                differences.append(f"{code} {row['sample_id']} {field}: "
                                   f"csv={row[field]!r} excel={_norm(cell)!r}")

    for code, (ws, _, tank_rows) in sheets.items():
        for (minute, tank), r in tank_rows.items():
            if _norm(ws.cell(r, TANKS[tank]["id"]).value) and (code, minute, tank) not in seen:
                differences.append(f"{code} minute {minute} {tank}: sample in the sheet but "
                                   f"missing from samples.csv")
    return checked


@dataclass(frozen=True)
class Comparison:
    """What was compared, and everywhere the CSV files and the workbook disagree."""
    values: int
    sheets: int
    differences: list[str]


def find_differences(workbook_path, data_dir):
    """Every value the CSV files and the workbook disagree on. Never raises.

    Walks the workbook itself rather than trusting the converter, so a value the
    converter never copied is reported too.
    """
    sheets = _index_sheets(openpyxl.load_workbook(workbook_path, data_only=True))
    differences = []
    values = (_compare_runs(sheets, data_dir / "runs.csv", differences)
              + _compare_stack(sheets, data_dir / "stack_readings.csv", differences)
              + _compare_tanks(sheets, data_dir / "tank_readings.csv", differences)
              + _compare_samples(sheets, data_dir / "samples.csv", differences))

    return Comparison(values=values, sheets=len(sheets), differences=differences)
