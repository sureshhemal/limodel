"""Check the CSV files against her workbook: every value must match its Excel cell.

Usage:
    uv run python scripts/verify_against_workbook.py "~/Downloads/ED_data_from M-V.xlsx"

Walks the workbook itself rather than trusting the converter, compares every value it
should have copied, and also reports anything in the sheets that did not reach the CSVs.
"""

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import openpyxl

CONC = {"id": 13, "cond": 14, "ph": 15, "temp": 16, "wt": 17,
        "li": 18, "na": 19, "mg": 20, "k": 21, "ca": 22, "toc": 23}
DIL = {"id": 24, "cond": 25, "ph": 26, "temp": 27, "wt": 28,
       "li": 29, "na": 30, "mg": 31, "k": 32, "ca": 33, "toc": 34}

HEADER_CELLS = [("run_date", 1, 2), ("li_feed_mg_l", 1, 5), ("mg_feed_mg_l", 2, 5),
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


def index_sheets(workbook):
    """code -> (sheet, {minute: row} for the main table, {minute: row} for the rinse block)."""
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
        main = {int(ws.cell(r, 2).value): r
                for r in range(9, rinse_row or ws.max_row + 1)
                if isinstance(ws.cell(r, 2).value, (int, float))}
        rinse = {}
        if rinse_row:
            for r in range(rinse_row, rinse_row + 12):
                minute = ws.cell(r, 2).value
                if not isinstance(minute, (int, float)):
                    break
                rinse[int(minute)] = r
        sheets[name.split("_")[-1]] = (ws, main, rinse)
    return sheets


def orphan_values(ws, row):
    """Lab values in a sheet row that carries no sample ID, so they belong to no sample."""
    found = []
    for prefix, cols in (("conc", CONC), ("dil", DIL)):
        if norm(ws.cell(row, cols["id"]).value):
            continue
        for measure in ("li", "na", "mg", "k", "ca", "toc"):
            value = norm(ws.cell(row, cols[measure]).value)
            if value:
                found.append(f"{prefix}_{measure}={value}")
    return found


def check_readings(sheets, path, problems):
    checked = 0
    seen = defaultdict(set)
    recorded = {}
    for row in csv.DictReader(open(path)):
        recorded[(row["experiment_code"], int(row["minute"]))] = (row["issue_code"], row["notes"])
        code, minute = row["experiment_code"], int(row["minute"])
        ws, main, rinse = sheets[code]
        if minute not in main:
            problems.append(f"{code} minute {minute}: no such row in the sheet")
            continue
        seen[code].add(minute)
        r = main[minute]
        pairs = [("supply_voltage_v", 3), ("supply_current_a", 4),
                 ("meter_voltage_v", 5), ("meter_current_ma", 6),
                 ("conc_conductivity_us_cm", CONC["cond"]), ("conc_ph", CONC["ph"]),
                 ("conc_temp_c", CONC["temp"]), ("conc_weight_g", CONC["wt"]),
                 ("dil_conductivity_us_cm", DIL["cond"]), ("dil_ph", DIL["ph"]),
                 ("dil_temp_c", DIL["temp"]), ("dil_weight_g", DIL["wt"]),
                 ("conc_sample_id", CONC["id"]), ("dil_sample_id", DIL["id"])]
        for field, col in pairs:
            checked += 1
            if not same(row[field], ws.cell(r, col).value):
                problems.append(f"{code} min {minute} {field}: "
                                f"csv={row[field]!r} excel={norm(ws.cell(r, col).value)!r}")
        rinse_row = rinse.get(minute)
        for field, key in [("rinse_conductivity_us_cm", "cond"), ("rinse_ph", "ph"),
                           ("rinse_temp_c", "temp"), ("rinse_weight_g", "wt"),
                           ("rinse_sample_id", "id")]:
            checked += 1
            expected = ws.cell(rinse_row, CONC[key]).value if rinse_row else None
            if not same(row[field], expected):
                problems.append(f"{code} min {minute} {field}: "
                                f"csv={row[field]!r} excel={norm(expected)!r}")

    for code, (ws, main, _) in sheets.items():
        columns = [3, 4, 5, 6] + list(CONC.values()) + list(DIL.values())
        for minute, r in main.items():
            has_data = any(ws.cell(r, c).value is not None for c in columns)
            if has_data and minute not in seen[code]:
                problems.append(f"{code} minute {minute}: has data in the sheet but is missing "
                                f"from readings.csv")
            # lab values with no sample ID are kept in the row's notes
            orphans = orphan_values(ws, r)
            issue_code, notes = recorded.get((code, minute), ("", ""))
            for value in orphans:
                checked += 1
                if value not in notes:
                    problems.append(f"{code} minute {minute}: sheet has {value} with no sample ID, "
                                    f"and it is not recorded in the CSV")
            if orphans and issue_code != "UNLABELLED_VALUES":
                problems.append(f"{code} minute {minute}: unlabelled lab values but "
                                f"issue_code is {issue_code!r}")
    return checked


def check_samples(sheets, path, problems):
    checked = 0
    seen = set()
    for row in csv.DictReader(open(path)):
        code, sample_id, tank = row["experiment_code"], row["sample_id"], row["tank"]
        ws, main, rinse = sheets[code]
        cols = DIL if tank == "dil" else CONC
        candidates = rinse.values() if tank == "rinse" else main.values()
        found = [r for r in candidates if norm(ws.cell(r, cols["id"]).value) == sample_id]
        if len(found) != 1:
            problems.append(f"{code} {sample_id} ({tank}): {len(found)} matching rows in the sheet")
            continue
        r = found[0]
        seen.add((code, sample_id))
        for field, key in [("li_mg_l", "li"), ("mg_mg_l", "mg"), ("na_mg_l", "na"),
                           ("k_mg_l", "k"), ("ca_mg_l", "ca"), ("toc_ppm", "toc")]:
            checked += 1
            if not same(row[field], ws.cell(r, cols[key]).value):
                problems.append(f"{code} {sample_id} {field}: "
                                f"csv={row[field]!r} excel={norm(ws.cell(r, cols[key]).value)!r}")

    for code, (ws, main, rinse) in sheets.items():
        for r in main.values():
            for cols in (CONC, DIL):
                sample_id = norm(ws.cell(r, cols["id"]).value)
                if sample_id and (code, sample_id) not in seen:
                    problems.append(f"{code} {sample_id}: in the sheet but missing from samples.csv")
        for r in rinse.values():
            sample_id = norm(ws.cell(r, CONC["id"]).value)
            if sample_id and (code, sample_id) not in seen:
                problems.append(f"{code} {sample_id}: rinse sample in the sheet but missing "
                                f"from samples.csv")
    return checked


def check_setups(sheets, path, problems):
    checked = 0
    codes_in_csv = set()
    for row in csv.DictReader(open(path)):
        codes_in_csv.add(row["code"])
        ws = sheets[row["code"]][0]
        for field, r, c in HEADER_CELLS:
            checked += 1
            value = ws.cell(r, c).value
            if field == "run_date" and hasattr(value, "date"):
                matches = row[field] == value.date().isoformat()
            else:
                matches = same(row[field], value)
            if not matches:
                problems.append(f"{row['code']} setup {field}: "
                                f"csv={row[field]!r} excel={norm(value)!r}")
        # the two fields read out of free text
        checked += 2
        text = norm(ws.cell(3, 9).value)
        match = re.search(r"([\d.]+)\s*g/?l\s*([A-Za-z0-9]+)", text, re.I)
        if match:
            amount, salt = match.groups()
            if row["conc_start_salt"] != salt or float(row["conc_start_g_l"]) != float(amount):
                problems.append(f"{row['code']} setup conc_start: "
                                f"csv={row['conc_start_salt']!r},{row['conc_start_g_l']} "
                                f"sheet text={text!r}")
        elif row["conc_start_salt"] or row["conc_start_g_l"]:
            problems.append(f"{row['code']} setup conc_start: csv has values, sheet text={text!r}")
        rinse_text = norm(ws.cell(5, 2).value)
        number = re.search(r"[\d.]+", rinse_text)
        if number and float(row["rinse_wt_pct"]) != float(number.group()):
            problems.append(f"{row['code']} setup rinse_wt_pct: "
                            f"csv={row['rinse_wt_pct']} sheet text={rinse_text!r}")
    for code in sheets:
        if code not in codes_in_csv:
            problems.append(f"{code}: sheet exists but has no row in setups.csv")
    return checked


def main(workbook_path, data_dir):
    workbook = openpyxl.load_workbook(workbook_path, data_only=True)
    sheets = index_sheets(workbook)
    problems = []
    checked = (check_setups(sheets, data_dir / "setups.csv", problems)
               + check_readings(sheets, data_dir / "readings.csv", problems)
               + check_samples(sheets, data_dir / "samples.csv", problems))
    print(f"compared {checked} values across {len(sheets)} sheets")
    print(f"{len(problems)} differences")
    for problem in problems:
        print(" ", problem)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]).expanduser(), Path(__file__).resolve().parent.parent / "data")
