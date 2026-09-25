"""Check the CSV files against her workbook: every value must match its Excel cell.

Usage:
    uv run python scripts/verify_against_workbook.py "~/Downloads/ED_data_from M-V.xlsx"

Walks the workbook itself rather than trusting the converter, compares every value it
should have copied, and reports anything in the sheets that did not reach the CSVs.
"""

import csv
import re
import sys
from pathlib import Path

import openpyxl

CONC = {"id": 13, "conductivity": 14, "ph": 15, "temp": 16, "weight": 17,
        "li": 18, "na": 19, "mg": 20, "k": 21, "ca": 22, "toc": 23}
DIL = {"id": 24, "conductivity": 25, "ph": 26, "temp": 27, "weight": 28,
       "li": 29, "na": 30, "mg": 31, "k": 32, "ca": 33, "toc": 34}
TANKS = {"conc": CONC, "dil": DIL, "rinse": CONC}

POWER = {"supply_voltage_v": 3, "supply_current_a": 4, "meter_voltage_v": 5, "meter_current_ma": 6}

TANK_MEASURES = {"conductivity_us_cm": "conductivity", "ph": "ph",
                 "temp_c": "temp", "weight_g": "weight"}
SAMPLE_MEASURES = {"li_mg_l": "li", "mg_mg_l": "mg", "na_mg_l": "na",
                   "k_mg_l": "k", "ca_mg_l": "ca", "toc_ppm": "toc"}
LAB_MEASURES = ("li", "na", "mg", "k", "ca", "toc")

RUN_CELLS = [("run_date", 1, 2), ("li_feed_mg_l", 1, 5), ("mg_feed_mg_l", 2, 5),
             ("licl_g_l", 3, 2), ("mgcl2_6h2o_g_l", 2, 2), ("cem", 1, 17), ("aem", 2, 17),
             ("flow_l_min", 1, 9), ("area_cm2", 2, 9), ("cell_pairs", 1, 13),
             ("tare_conc_g", 2, 25), ("tare_dil_g", 3, 25), ("tare_rinse_g", 4, 25)]


def norm(value):
    """Excel value as the string a faithful CSV would hold."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def same(csv_value, excel_value):
    written, expected = csv_value.strip(), norm(excel_value)
    if written == expected:
        return True
    try:
        return abs(float(written) - float(expected)) < 1e-12
    except (ValueError, TypeError):
        return False


def read_rows(path):
    return list(csv.DictReader(open(path)))


def orphan_values(ws, row, cols):
    """Lab values in a sheet row that carries no sample ID."""
    if norm(ws.cell(row, cols["id"]).value):
        return []
    return [f"{m}={norm(ws.cell(row, cols[m]).value)}"
            for m in LAB_MEASURES if norm(ws.cell(row, cols[m]).value)]


def index_sheets(workbook):
    """code -> (sheet, {minute: row}, {(minute, tank): row})."""
    sheets = {}
    for name in workbook.sheetnames:
        if not name.startswith("New_set"):
            continue
        ws = workbook[name]
        rinse_row = None
        for r in range(9, ws.max_row + 1):
            if str(ws.cell(r, 1).value).strip().lower() == "rinse":
                rinse_row = r
                break

        stack_rows, tank_rows = {}, {}
        for r in range(9, rinse_row or ws.max_row + 1):
            minute = ws.cell(r, 2).value
            if isinstance(minute, (int, float)):
                stack_rows[int(minute)] = r
                tank_rows[(int(minute), "conc")] = r
                tank_rows[(int(minute), "dil")] = r
        if rinse_row:
            for r in range(rinse_row, rinse_row + 12):
                minute = ws.cell(r, 2).value
                if not isinstance(minute, (int, float)):
                    break
                tank_rows[(int(minute), "rinse")] = r

        sheets[name.split("_")[-1]] = (ws, stack_rows, tank_rows)
    return sheets


def check_runs(sheets, path, problems):
    checked = 0
    in_csv = set()
    for row in read_rows(path):
        in_csv.add(row["run_code"])
        ws = sheets[row["run_code"]][0]
        for field, r, c in RUN_CELLS:
            checked += 1
            value = ws.cell(r, c).value
            if field == "run_date" and hasattr(value, "date"):
                matches = row[field] == value.date().isoformat()
            else:
                matches = same(row[field], value)
            if not matches:
                problems.append(f"{row['run_code']} run {field}: "
                                f"csv={row[field]!r} excel={norm(value)!r}")
        checked += 2
        text = norm(ws.cell(3, 9).value)
        match = re.search(r"([\d.]+)\s*g/?l\s*([A-Za-z0-9]+)", text, re.I)
        if match:
            amount, salt = match.groups()
            if row["conc_start_salt"] != salt or float(row["conc_start_g_l"]) != float(amount):
                problems.append(f"{row['run_code']} run conc_start: "
                                f"csv={row['conc_start_salt']!r},{row['conc_start_g_l']} "
                                f"sheet text={text!r}")
        rinse_text = norm(ws.cell(5, 2).value)
        number = re.search(r"[\d.]+", rinse_text)
        if number and float(row["rinse_wt_pct"]) != float(number.group()):
            problems.append(f"{row['run_code']} run rinse_wt_pct: "
                            f"csv={row['rinse_wt_pct']} sheet text={rinse_text!r}")
    for code in sheets:
        if code not in in_csv:
            problems.append(f"{code}: sheet exists but has no row in runs.csv")
    return checked


def check_stack(sheets, path, problems):
    checked = 0
    seen = set()
    for row in read_rows(path):
        code, minute = row["run_code"], int(row["minute"])
        ws, stack_rows, _ = sheets[code]
        if minute not in stack_rows:
            problems.append(f"{code} minute {minute}: no such row in the sheet")
            continue
        seen.add((code, minute))
        r = stack_rows[minute]
        for field, column in POWER.items():
            checked += 1
            if not same(row[field], ws.cell(r, column).value):
                problems.append(f"{code} min {minute} {field}: "
                                f"csv={row[field]!r} excel={norm(ws.cell(r, column).value)!r}")

    for code, (ws, stack_rows, _) in sheets.items():
        for minute, r in stack_rows.items():
            has_power = any(ws.cell(r, c).value is not None for c in POWER.values())
            if has_power and (code, minute) not in seen:
                problems.append(f"{code} minute {minute}: power readings in the sheet but "
                                f"missing from stack_readings.csv")
    return checked


def check_tanks(sheets, path, problems):
    checked = 0
    seen = set()
    for row in read_rows(path):
        code, minute, tank = row["run_code"], int(row["minute"]), row["tank"]
        ws, _, tank_rows = sheets[code]
        r = tank_rows.get((minute, tank))
        if r is None:
            problems.append(f"{code} minute {minute} {tank}: no such row in the sheet")
            continue
        seen.add((code, minute, tank))
        cols = TANKS[tank]
        for field, key in TANK_MEASURES.items():
            checked += 1
            if not same(row[field], ws.cell(r, cols[key]).value):
                problems.append(f"{code} min {minute} {tank} {field}: "
                                f"csv={row[field]!r} excel={norm(ws.cell(r, cols[key]).value)!r}")
        # lab values with no sample ID are kept here, in notes
        for value in orphan_values(ws, r, cols):
            checked += 1
            if value not in row["notes"]:
                problems.append(f"{code} minute {minute} {tank}: sheet has {value} with no "
                                f"sample ID, and it is not recorded in the CSV")

    for code, (ws, _, tank_rows) in sheets.items():
        for (minute, tank), r in tank_rows.items():
            cols = TANKS[tank]
            has_value = any(ws.cell(r, cols[k]).value is not None for k in TANK_MEASURES.values())
            if (has_value or orphan_values(ws, r, cols)) and (code, minute, tank) not in seen:
                problems.append(f"{code} minute {minute} {tank}: values in the sheet but "
                                f"missing from tank_readings.csv")
    return checked


def check_samples(sheets, path, problems):
    checked = 0
    seen = set()
    for row in read_rows(path):
        code, minute, tank = row["run_code"], int(row["minute"]), row["tank"]
        ws, _, tank_rows = sheets[code]
        r = tank_rows.get((minute, tank))
        if r is None:
            problems.append(f"{code} {row['sample_id']}: no row in the sheet at "
                            f"minute {minute} {tank}")
            continue
        seen.add((code, minute, tank))
        cols = TANKS[tank]
        checked += 1
        if row["sample_id"] != norm(ws.cell(r, cols["id"]).value):
            problems.append(f"{code} min {minute} {tank} sample_id: csv={row['sample_id']!r} "
                            f"excel={norm(ws.cell(r, cols['id']).value)!r}")
        for field, key in SAMPLE_MEASURES.items():
            checked += 1
            if not same(row[field], ws.cell(r, cols[key]).value):
                problems.append(f"{code} {row['sample_id']} {field}: "
                                f"csv={row[field]!r} excel={norm(ws.cell(r, cols[key]).value)!r}")

    for code, (ws, _, tank_rows) in sheets.items():
        for (minute, tank), r in tank_rows.items():
            if norm(ws.cell(r, TANKS[tank]["id"]).value) and (code, minute, tank) not in seen:
                problems.append(f"{code} minute {minute} {tank}: sample in the sheet but "
                                f"missing from samples.csv")
    return checked


def main(workbook_path, data_dir):
    workbook = openpyxl.load_workbook(workbook_path, data_only=True)
    sheets = index_sheets(workbook)
    problems = []
    checked = (check_runs(sheets, data_dir / "runs.csv", problems)
               + check_stack(sheets, data_dir / "stack_readings.csv", problems)
               + check_tanks(sheets, data_dir / "tank_readings.csv", problems)
               + check_samples(sheets, data_dir / "samples.csv", problems))
    print(f"compared {checked} values across {len(sheets)} sheets")
    print(f"{len(problems)} differences")
    for problem in problems:
        print(" ", problem)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]).expanduser(), Path(__file__).resolve().parent.parent / "data")
