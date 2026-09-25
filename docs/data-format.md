# Data format

How her experiment data is stored, and how to create the files for a new run.
See the [README](../README.md) for the project as a whole.

## The four files

The CSV files hold only what was set, measured at the rig, or reported by the lab. Every derived number is calculated by the code. To correct a value, edit the source and run the converter again; everything downstream updates.

| File | One row per | Contents | Recorded |
|---|---|---|---|
| `runs.csv` | experiment | Membranes, feed, starting concentrate, rinse, flow, area, cell pairs, tare weights | before the run |
| `stack_readings.csv` | time mark of a run | The power log: supply and multimeter voltage and current | during the run |
| `tank_readings.csv` | tank at a time mark | Conductivity, pH, temperature, weight for one of concentrate, diluate or rinse | during the run |
| `samples.csv` | sample | Li, Mg, Na, K, Ca (ICP) and TOC | by the lab, later |

```
runs ──< stack_readings
     ──< tank_readings ──0..1── samples
```

- `run_code` says which run a row belongs to, and must match a `code` in `runs.csv`.
- A tank reading is identified by `run_code, minute, tank`.
- A sample is **identified by where and when it was taken** — the same `run_code, minute, tank` — so its tank is recorded once, not twice. `sample_id` is its label from the lab and is unique across all runs.

Rules for every file:

- Blank means not measured. Never enter 0 for a missing value.
- No calculated columns. Volumes, current density, charge, flux, t, P and recovery come from the code, so they cannot drift from the raw values.
- Units go in column names only; cells hold plain numbers, with a dot for decimals.
- Same headers, same order, in every file.
- Membrane names and sample IDs are spelled exactly as recorded.
- Runs that should not be used get `include = false` and a reason in `notes`; they are never deleted.

## Column definitions

### `runs.csv`

| Column | Type | Unit | Required | Meaning |
|---|---|---|---|---|
| `run_code` | text, primary key | | ✓ | Short experiment code, e.g. `AE` |
| `series` | text | | ✓ | Group of related runs |
| `run_date` | date | YYYY-MM-DD | ✓ | Date of the run |
| `cem` | text | | ✓ | Cation exchange membrane |
| `aem` | text | | ✓ | Anion exchange membrane |
| `li_feed_mg_l` | numeric | mg/L | ✓ | Nominal Li in the feed; the measured value is the t = 0 diluate sample |
| `mg_feed_mg_l` | numeric | mg/L | ✓ | Nominal Mg in the feed |
| `licl_g_l` | numeric | g/L | | LiCl actually weighed in |
| `mgcl2_6h2o_g_l` | numeric | g/L | | MgCl₂·6H₂O actually weighed in |
| `conc_start_salt` | text | | ✓ | Salt the concentrate started with |
| `conc_start_g_l` | numeric | g/L | ✓ | How much of it |
| `rinse_salt` | text | | ✓ | Electrode rinse salt |
| `rinse_wt_pct` | numeric | wt% | ✓ | Its concentration |
| `set_current_ma` | numeric | mA | | Current set on the supply; the actual current comes from the readings |
| `flow_l_min` | numeric | L/min | ✓ | Flow rate of each stream |
| `area_cm2` | numeric | cm² | ✓ | Membrane area per cell pair |
| `cell_pairs` | integer | | ✓ | Number of cell pairs |
| `tare_conc_g` | numeric | g | ✓ | Concentrate bucket + stirrer, for this run |
| `tare_dil_g` | numeric | g | ✓ | Diluate bucket + stirrer |
| `tare_rinse_g` | numeric | g | ✓ | Rinse bucket + stirrer |
| `include` | boolean | | ✓ | Whether the run is used |
| `notes` | text | | | |

Not stored, because the code calculates them: Mg/Li mass and molar ratio, flow in cm³/s, velocity, current density, total charge, run length.

### `stack_readings.csv`

| Column | Type | Unit | Meaning |
|---|---|---|---|
| `run_code` | text → `runs.run_code` | | Which run |
| `minute` | integer | min | Elapsed time; unique within a run |
| `supply_voltage_v` | numeric | V | Power supply. The value at minute 0 is what the ≤ 20 V gate uses. |
| `supply_current_a` | numeric | A | Power supply |
| `meter_voltage_v` | numeric | V | Multimeter |
| `meter_current_ma` | numeric | mA | Multimeter; this is the current used in the calculations |
| `notes` | text | | |

### `tank_readings.csv`

| Column | Type | Unit | Meaning |
|---|---|---|---|
| `run_code` | text → `runs.run_code` | | Which run |
| `minute` | integer | min | Elapsed time |
| `tank` | text | | `conc`, `dil` or `rinse` |
| `conductivity_us_cm` | numeric | µS/cm | |
| `ph` | numeric | | |
| `temp_c` | numeric | °C | |
| `weight_g` | numeric | g | Including bucket and stirrer. Volume = (weight − tare) / 1000. |
| `notes` | text | | |

Unique on `run_code, minute, tank`.

### `samples.csv`

| Column | Type | Unit | Meaning |
|---|---|---|---|
| `sample_id` | text, unique across all runs | | The lab's label, e.g. `AE1` |
| `run_code` | text → `runs.run_code` | | Which run |
| `minute` | integer | min | When it was drawn |
| `tank` | text | | Which tank it came from |
| `li_mg_l` | numeric | mg/L | Li, by ICP |
| `mg_mg_l` | numeric | mg/L | Mg, by ICP |
| `na_mg_l`, `k_mg_l`, `ca_mg_l` | numeric | mg/L | Blank when not measured; kept for future Na or seawater runs |
| `toc_ppm` | numeric | ppm | Total organic carbon |
| `notes` | text | | |

`run_code, minute, tank` points at a row in `tank_readings.csv`.

## Creating the CSV files from a run

### Converting with the script

`scripts/convert_workbook.py` converts every `New_set_*` sheet in one go:

```
uv run python scripts/convert_workbook.py "~/Downloads/ED_data_from M-V.xlsx"
```

It rewrites all four files and prints anything that looks wrong: sample IDs that do not carry their run's code, lab values with no sample ID, and samples still waiting on the lab. `limodel check` reports the same kinds of problem from the CSV files themselves. **It copies values exactly as they appear in the sheet** — no spelling is corrected, no stale value is replaced, nothing is filled in. Problems are reported, never fixed, so the files stay a faithful copy of what she recorded.

Re-run it whenever she updates the workbook. Because the output is committed to git, the diff then shows exactly which values changed.

### Checking the copy

```
uv run python scripts/verify_against_workbook.py "~/Downloads/ED_data_from M-V.xlsx"
```

It walks the workbook itself rather than trusting the converter, compares every value against the cell it came from, and reports anything in the sheets that did not reach the CSVs.

### Where the values are in her spreadsheet

Each `New_set_Mg2+(…)_<CODE>` sheet has the same layout.

**Header block (rows 1–5) → the `runs.csv` row**

| Value | Cell |
|---|---|
| Date | B1 |
| Li feed / Mg feed (mg/L) | E1 / E2 |
| LiCl weighed in (g/L) | B3 |
| CEM / AEM | Q1 / Q2 |
| Flow rate (L/min) | I1 |
| Area per cell pair (cm²) | I2 |
| Cell pairs | M1 |
| Starting concentrate | I3, e.g. "DI Water +0.5 g/l LiCl" → `LiCl`, `0.5` |
| Rinse solution | A5 / B5 |
| Tares: conc / dil / rinse (g) | Y2 / Y3 / Y4 |

**Main table (from row 9)**

| Block | Columns | Goes to |
|---|---|---|
| Time and power | A (hour), B (minute), C (supply V), D (supply A), E (multimeter V), F (multimeter mA) | `stack_readings.csv` |
| Hourly summary | G–L | **skipped** — the code calculates these |
| Concentrate | M (sample ID), N (conductivity), O (pH), P (temperature), Q (weight), R–W (lab results) | `tank_readings.csv` + `samples.csv`, tank `conc` |
| Diluate | X (sample ID), Y, Z, AA, AB, AC–AH | `tank_readings.csv` + `samples.csv`, tank `dil` |

**Rinse block** — below the main table, starting at the row whose column A says `Rinse`. Its position depends on the run length (about row 36 for a 3-sample run, 56 for 5, 88 for 7, 120 for 9). It reuses the concentrate columns, and its rows match the main table by minute. Goes to `tank_readings.csv` and `samples.csv` with tank `rinse`.

Anything below the rinse block (the I–V sweep, the limiting-current table, the summary tables to the right) is **not** copied.

Sample IDs run two per sampling time: odd numbers are concentrate, even are diluate, and the rinse starts at 17 (or 19 in runs with nine sampling times, where the main table has used 1–18). Gaps in the numbering are normal.

### Things to watch for

- **Sample IDs must carry the run's own code.** Mislabelled IDs have already appeared in her sheets (`J10` for `AJ10`, `K18` for `AK18`, and a whole rinse block labelled with the previous run's code).
- **Copy raw readings, never the calculated block.** Some calculated cells in her sheet have values typed over the formula, so they disagree with the raw reading they came from.
- **Blank, never 0**, for a measurement that wasn't taken.
- **Use the measured feed.** The nominal feed goes in `runs.csv`; the real feed concentration is the t = 0 diluate sample.
- **Tares change between runs**, so take them from that run's own header block.
- **Different starting concentrate** (a different salt or strength) makes a run not comparable with the rest. Record it in `conc_start_salt` / `conc_start_g_l` and consider `include = false`.
