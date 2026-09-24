"""Convert her Excel workbook into data/setups.csv, data/readings.csv and data/samples.csv.

Usage:
    uv run python scripts/convert_workbook.py "~/Downloads/ED_data_from M-V.xlsx"

Reads every `New_set_*` sheet, writes the three CSV files, and prints anything that
looks wrong (sample IDs that do not carry the run's code, missing lab results).
The layout it expects is described in docs/data-format.md.
"""

import csv
import re
import sys
from pathlib import Path

import openpyxl

# Column numbers in her sheets. The rinse block reuses the concentrate columns.
POWER = {"supply_voltage_v": 3, "supply_current_a": 4, "meter_voltage_v": 5, "meter_current_ma": 6}
CONC = {"id": 13, "conductivity": 14, "ph": 15, "temp": 16, "weight": 17,
        "li": 18, "na": 19, "mg": 20, "k": 21, "ca": 22, "toc": 23}
DIL = {"id": 24, "conductivity": 25, "ph": 26, "temp": 27, "weight": 28,
       "li": 29, "na": 30, "mg": 31, "k": 32, "ca": 33, "toc": 34}

# Issue codes the script can set by itself. checks.py decides what each one means.
UNLABELLED_VALUES = "UNLABELLED_VALUES"  # lab values in a row that carries no sample ID

SETUP_FIELDS = ["code", "series", "run_date", "cem", "aem", "li_feed_mg_l", "mg_feed_mg_l",
                "licl_g_l", "mgcl2_6h2o_g_l", "conc_start_salt", "conc_start_g_l",
                "rinse_salt", "rinse_wt_pct", "set_current_ma", "flow_l_min", "area_cm2",
                "cell_pairs", "tare_conc_g", "tare_dil_g", "tare_rinse_g", "include", "issue_code", "notes"]

READING_FIELDS = (["experiment_code", "minute"] + list(POWER)
                  + [f"{t}_{m}" for t in ("conc", "dil", "rinse")
                     for m in ("conductivity_us_cm", "ph", "temp_c", "weight_g")]
                  + ["conc_sample_id", "dil_sample_id", "rinse_sample_id", "issue_code", "notes"])

SAMPLE_FIELDS = ["experiment_code", "sample_id", "tank", "li_mg_l", "mg_mg_l",
                 "na_mg_l", "k_mg_l", "ca_mg_l", "toc_ppm", "issue_code", "notes"]


def plain(number):
    """Write 2.0 as 2, so values look as they do in the sheet."""
    return int(number) if float(number).is_integer() else number


IGNORED_WHEN_EMPTY = {"experiment_code", "minute", "issue_code", "notes"}


def blank(value):
    """Excel cell to CSV value: None and empty strings become blank."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return value


def code_of(sheet_name):
    return sheet_name.strip().split("_")[-1]



def find_rinse_row(ws):
    """Row where the rinse block starts, found by the 'Rinse' label in column A."""
    for r in range(9, ws.max_row + 1):
        if str(ws.cell(r, 1).value).strip().lower() == "rinse":
            return r
    return None


def parse_conc_start(text):
    """'DI Water +0.5 g/l LiCl' -> ('LiCl', 0.5), keeping the salt spelled as she wrote it."""
    if not text:
        return "", ""
    match = re.search(r"([\d.]+)\s*g/?l\s*([A-Za-z0-9]+)", str(text), re.I)
    if not match:
        return "", ""
    amount, salt = match.groups()
    return salt, plain(float(amount))


def read_setup(ws, code):
    date = ws.cell(1, 2).value
    salt, amount = parse_conc_start(ws.cell(3, 9).value)
    rinse_pct = re.search(r"[\d.]+", str(ws.cell(5, 2).value or ""))
    return {
        "code": code,
        "series": "new_set_mg",
        "run_date": date.date().isoformat() if hasattr(date, "date") else blank(date),
        "cem": blank(ws.cell(1, 17).value),
        "aem": blank(ws.cell(2, 17).value),
        "li_feed_mg_l": blank(ws.cell(1, 5).value),
        "mg_feed_mg_l": blank(ws.cell(2, 5).value),
        "licl_g_l": blank(ws.cell(3, 2).value),
        "mgcl2_6h2o_g_l": blank(ws.cell(2, 2).value),
        "conc_start_salt": salt,
        "conc_start_g_l": amount,
        "rinse_salt": blank(ws.cell(5, 1).value),
        "rinse_wt_pct": plain(float(rinse_pct.group())) if rinse_pct else "",
        "set_current_ma": "",
        "flow_l_min": blank(ws.cell(1, 9).value),
        "area_cm2": blank(ws.cell(2, 9).value),
        "cell_pairs": blank(ws.cell(1, 13).value),
        "tare_conc_g": blank(ws.cell(2, 25).value),
        "tare_dil_g": blank(ws.cell(3, 25).value),
        "tare_rinse_g": blank(ws.cell(4, 25).value),
        "include": "true",
        "issue_code": "",
        "notes": "",
    }


def read_tank(ws, row, cols):
    return {
        "id": blank(ws.cell(row, cols["id"]).value),
        "conductivity_us_cm": blank(ws.cell(row, cols["conductivity"]).value),
        "ph": blank(ws.cell(row, cols["ph"]).value),
        "temp_c": blank(ws.cell(row, cols["temp"]).value),
        "weight_g": blank(ws.cell(row, cols["weight"]).value),
    }


def orphan_values(ws, row):
    """Lab values sitting in a row that has no sample ID, so they belong to no sample."""
    found = []
    for prefix, cols in (("conc", CONC), ("dil", DIL)):
        if blank(ws.cell(row, cols["id"]).value):
            continue
        for measure in ("li", "na", "mg", "k", "ca", "toc"):
            value = blank(ws.cell(row, cols[measure]).value)
            if value != "":
                found.append(f"{prefix}_{measure}={value}")
    return found


def read_sample(ws, row, cols, code, tank):
    return {
        "experiment_code": code,
        "sample_id": blank(ws.cell(row, cols["id"]).value),
        "tank": tank,
        "li_mg_l": blank(ws.cell(row, cols["li"]).value),
        "mg_mg_l": blank(ws.cell(row, cols["mg"]).value),
        "na_mg_l": blank(ws.cell(row, cols["na"]).value),
        "k_mg_l": blank(ws.cell(row, cols["k"]).value),
        "ca_mg_l": blank(ws.cell(row, cols["ca"]).value),
        "toc_ppm": blank(ws.cell(row, cols["toc"]).value),
        "issue_code": "",
        "notes": "",
    }


def convert_sheet(ws, code):
    """One sheet -> (setup row, reading rows, sample rows, warnings)."""
    rinse_row = find_rinse_row(ws)
    end = rinse_row if rinse_row else ws.max_row + 1
    warnings = []

    rinse_by_minute, rinse_samples, samples = {}, [], []
    if rinse_row:
        for r in range(rinse_row, rinse_row + 12):
            minute = ws.cell(r, 2).value
            if not isinstance(minute, (int, float)):
                break
            rinse_by_minute[int(minute)] = read_tank(ws, r, CONC)
            if blank(ws.cell(r, CONC["id"]).value):
                rinse_samples.append(read_sample(ws, r, CONC, code, "rinse"))

    readings = []
    for r in range(9, end):
        minute = ws.cell(r, 2).value
        if not isinstance(minute, (int, float)):
            continue
        conc, dil = read_tank(ws, r, CONC), read_tank(ws, r, DIL)
        rinse = rinse_by_minute.get(int(minute), {})
        row = {"experiment_code": code, "minute": int(minute), "issue_code": "", "notes": ""}
        for field, col in POWER.items():
            row[field] = blank(ws.cell(r, col).value)
        for prefix, tank in (("conc", conc), ("dil", dil), ("rinse", rinse)):
            for measure in ("conductivity_us_cm", "ph", "temp_c", "weight_g"):
                row[f"{prefix}_{measure}"] = tank.get(measure, "")
            row[f"{prefix}_sample_id"] = tank.get("id", "")
        orphans = orphan_values(ws, r)
        has_readings = any(row[f] != "" for f in READING_FIELDS if f not in IGNORED_WHEN_EMPTY)
        if orphans:
            values = ", ".join(orphans)
            row["issue_code"] = UNLABELLED_VALUES
            row["notes"] = values
            warnings.append(f"{code}: minute {int(minute)} has {values} but no sample ID")
        if orphans or has_readings:
            readings.append(row)
        if conc["id"]:
            samples.append(read_sample(ws, r, CONC, code, "conc"))
        if dil["id"]:
            samples.append(read_sample(ws, r, DIL, code, "dil"))

    samples.extend(rinse_samples)

    for sample in samples:
        if not sample["sample_id"].upper().startswith(code.upper()):
            warnings.append(f"{code}: sample ID {sample['sample_id']!r} does not start with {code}")
        if sample["li_mg_l"] == "" and sample["mg_mg_l"] == "":
            warnings.append(f"{code}: sample {sample['sample_id']} has no lab results yet")

    return read_setup(ws, code), readings, samples, warnings


def write_csv(path, fields, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{path}: {len(rows)} rows")


def main(workbook_path, out_dir):
    workbook = openpyxl.load_workbook(workbook_path, data_only=True)
    setups, readings, samples, warnings = [], [], [], []
    for name in workbook.sheetnames:
        if not name.startswith("New_set"):
            continue
        setup, run_readings, run_samples, run_warnings = convert_sheet(workbook[name], code_of(name))
        setups.append(setup)
        readings.extend(run_readings)
        samples.extend(run_samples)
        warnings.extend(run_warnings)
        print(f"{setup['code']:3s} {len(run_readings):3d} readings  {len(run_samples):2d} samples")

    write_csv(out_dir / "setups.csv", SETUP_FIELDS, setups)
    write_csv(out_dir / "readings.csv", READING_FIELDS, readings)
    write_csv(out_dir / "samples.csv", SAMPLE_FIELDS, samples)

    if warnings:
        print(f"\n{len(warnings)} warnings:")
        for warning in warnings:
            print(" ", warning)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]).expanduser(), Path(__file__).resolve().parent.parent / "data")
