# Data format

How her experiment data is stored, and how to create the files for a new run.
See the [README](../README.md) for the project as a whole.

## The three files

The CSV files hold only what was set, measured at the rig, or reported by the lab. Every derived number is calculated by the code. To correct a value, edit the CSV and run again; everything downstream updates.

| File | One row per | Contents | Recorded |
|---|---|---|---|
| `setups.csv` | experiment | Membranes, feed, starting concentrate, rinse, flow, area, cell pairs, tare weights, `include`, `notes` | before the run |
| `readings.csv` | time mark of a run | Power log (supply and multimeter V/I); tank conductivity, pH, temperature, weight; IDs of samples taken | during the run |
| `samples.csv` | sample | Which tank the sample came from, plus Li, Mg, Na, K, Ca (ICP) and TOC, by `sample_id` | by the lab, later |

All runs share the same two files; `experiment_code` says which run a row belongs to, and it must match a `code` in `setups.csv`. Each file is one future PostgreSQL table. A sample's time comes from the readings file, through `conc_sample_id`, `dil_sample_id` and `rinse_sample_id`; those columns are also what decides which tank a sample belongs to. The samples file repeats the tank in its own `tank` column (`conc` / `dil` / `rinse`) so the lab results are readable on their own — it is a cross-check, not the authority, and `checks.py` reports any sample where the two disagree.

Rules:

- Blank means not measured. Never enter 0 for a missing value.
- No calculated columns.
- Units go in column names only; cells hold plain numbers.
- Same headers, same order, in every file.
- Membrane names and sample IDs are spelled exactly the same everywhere.
- Runs that shouldn't be used get `include = false` and a reason in `notes`. They are never deleted.

## Column definitions

### `setups.csv`

One row per experiment. Only values that were set or weighed out go here. Derived values (Mg/Li mass and molar ratio, flow in cm³/s, velocity, current density, total charge, run length) are calculated by the code.

| Column | Type | Unit | Required | Meaning | Example |
|---|---|---|---|---|---|
| `code` | text, unique | | ✓ | Short experiment code. Names the readings and samples files. | `AE` |
| `series` | text | | ✓ | Group of related runs, so different campaigns stay apart | `new_set_mg` |
| `run_date` | date | YYYY-MM-DD | ✓ | Date the run was carried out | `2026-07-09` |
| `cem` | text | | ✓ | Cation exchange membrane | `GO-10` |
| `aem` | text | | ✓ | Anion exchange membrane | `AR 204` |
| `li_feed_mg_l` | numeric | mg/L | ✓ | Nominal (target) Li in the feed. The measured value comes from the t = 0 diluate sample. | `400` |
| `mg_feed_mg_l` | numeric | mg/L | ✓ | Nominal (target) Mg in the feed | `2000` |
| `licl_g_l` | numeric | g/L | | LiCl actually weighed into the feed | `2.44` |
| `mgcl2_6h2o_g_l` | numeric | g/L | | MgCl₂·6H₂O actually weighed into the feed | |
| `conc_start_salt` | text | | ✓ | Salt the concentrate started with: `LiCl`, `NaCl` or `none` | `LiCl` |
| `conc_start_g_l` | numeric | g/L | ✓ | Amount of that salt in the starting concentrate (0 if `none`) | `0.5` |
| `rinse_salt` | text | | ✓ | Salt in the electrode rinse solution | `Na2SO4` |
| `rinse_wt_pct` | numeric | wt% | ✓ | Rinse salt concentration | `2` |
| `set_current_ma` | numeric | mA | | Current set on the power supply. The actual current comes from the readings. | |
| `flow_l_min` | numeric | L/min | ✓ | Flow rate of each stream | `0.2` |
| `area_cm2` | numeric | cm² | ✓ | Effective membrane area per cell pair | `6` |
| `cell_pairs` | integer | | ✓ | Number of cell pairs in the stack | `10` |
| `tare_conc_g` | numeric | g | ✓ | Concentrate bucket + stirrer weight for this run. Subtracted from tank weights to get volume. | `96.2` |
| `tare_dil_g` | numeric | g | ✓ | Diluate bucket + stirrer weight for this run | `111.5` |
| `tare_rinse_g` | numeric | g | ✓ | Rinse bucket + stirrer weight for this run | `42` |
| `include` | boolean | `true` / `false` | ✓ | Whether the run is used in the model. Excluded runs stay in the file. | `true` |
| `notes` | text | | | Why a run is excluded, or anything unusual about it | |

### `readings.csv`

One row per time mark of a run. Everything recorded at the rig. Blank where a value was not measured at that minute.

| Column | Type | Unit | Meaning |
|---|---|---|---|
| `experiment_code` | text → `setups.code` | | Which run this row belongs to |
| `minute` | integer | min | Elapsed time from the start of the run. Unique within a run. |
| `supply_voltage_v` | numeric | V | Power supply voltage. The value at minute 0 is what the ≤ 20 V gate uses. |
| `supply_current_a` | numeric | A | Power supply current |
| `meter_voltage_v` | numeric | V | Multimeter voltage |
| `meter_current_ma` | numeric | mA | Multimeter current. This is the current used in the calculations. |
| `conc_conductivity_us_cm` | numeric | µS/cm | Concentrate tank |
| `conc_ph` | numeric | | Concentrate tank |
| `conc_temp_c` | numeric | °C | Concentrate tank |
| `conc_weight_g` | numeric | g | Concentrate tank, including bucket and stirrer. Volume = (weight − `tare_conc_g`) / 1000. |
| `dil_conductivity_us_cm`, `dil_ph`, `dil_temp_c`, `dil_weight_g` | numeric | as above | Diluate tank |
| `rinse_conductivity_us_cm`, `rinse_ph`, `rinse_temp_c`, `rinse_weight_g` | numeric | as above | Electrode rinse |
| `conc_sample_id` | text | | ID of the concentrate sample taken at this minute, otherwise blank |
| `dil_sample_id` | text | | ID of the diluate sample taken at this minute |
| `rinse_sample_id` | text | | ID of the rinse sample taken at this minute |
| `notes` | text | | Anything unusual at this time mark |

### `samples.csv`

One row per sample. Lab results, usually filled in days after the run.

| Column | Type | Unit | Meaning |
|---|---|---|---|
| `experiment_code` | text → `setups.code` | | Which run the sample came from |
| `sample_id` | text, unique across all runs | | Must match the ID in `readings.csv` exactly |
| `tank` | text | | `conc`, `dil` or `rinse`. A cross-check against the readings file, which stays the authority. |
| `li_mg_l` | numeric | mg/L | Li, by ICP |
| `mg_mg_l` | numeric | mg/L | Mg, by ICP |
| `na_mg_l`, `k_mg_l`, `ca_mg_l` | numeric | mg/L | Other cations by ICP. Blank when not measured; kept for future Na or seawater runs. |
| `toc_ppm` | numeric | ppm | Total organic carbon |
| `notes` | text | | e.g. dilution applied, sample re-run |

## Creating the CSV files from a run

Each run becomes three things: one row in `setups.csv`, one readings file and one samples file. The experiment code (`AE`, `AF`, …) ties them together and gives the two files their names.

### Where the values are in her spreadsheet

Each `New_set_Mg2+(…)_<CODE>` sheet has the same layout.

**Header block (rows 1–5) → the `setups.csv` row**

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

The Mg/Li mass ratio (E3), molar ratio (E4), flow in cm³/s (M2) and velocity (M5) are **not** copied. The code calculates them.

**Main table (from row 9) → the readings file**

| Block | Columns | Goes to |
|---|---|---|
| Time and power | A (hour), B (minute), C (supply V), D (supply A), E (multimeter V), F (multimeter mA) | `minute`, `supply_*`, `meter_*` |
| Hourly summary | G–L (average current, current density, charge, equivalents, average voltage, Wh) | **skipped** — the code calculates these |
| Concentrate | M (sample ID), N (conductivity), O (pH), P (temperature), Q (weight) | `conc_*` |
| Diluate | X (sample ID), Y, Z, AA, AB | `dil_*` |

**Rinse block** — below the main table, starting at the row whose column A says `Rinse`. Its position depends on the run length (about row 36 for a 3-sample run, 56 for 5, 88 for 7, 120 for 9). It reuses the concentrate columns: M (sample ID), N (conductivity), O (pH), Q (weight). Match its rows to the main table by minute and fill the `rinse_*` columns.

Anything below the rinse block (the I–V sweep, the limiting-current table, the summary tables to the right) is **not** copied.

**Lab results → the samples file**

| Tank | Sample ID | Li | Mg | Na | K | Ca | TOC |
|---|---|---|---|---|---|---|---|
| Concentrate | M | R | T | S | U | V | W |
| Diluate | X | AC | AE | AD | AF | AG | AH |
| Rinse | M (rinse block) | R | T | S | U | V | W |

Sample IDs run two per sampling time: odd numbers are concentrate, even are diluate, and the rinse starts at 17 (or 19 in runs with nine sampling times, where the main table has used 1–18). Gaps in the numbering are normal.

### Steps

1. **Add the `setups.csv` row** from the header block. Set `include` to `true`, and add a `notes` entry if anything about the run was unusual.
2. **Append the run's rows to `data/readings.csv`**, one per time mark that has any value, each starting with the experiment code. Skip rows where only the time was written down.
3. **Merge the rinse block in** by minute, into the `rinse_*` columns of the rows that already exist.
4. **Append the run's samples to `data/samples.csv`**, one row per sample ID, with the experiment code, the tank, and whatever the lab reported. Leave a cell blank when a measurement wasn't done.
5. **Run the checks** and fix whatever they report.
6. **Commit** the three files, so every later correction is recorded as a change.

### Things to watch for

- **Sample IDs must carry the run's own code.** Mislabelled IDs have already appeared in her sheets (`J10` for `AJ10`, `K18` for `AK18`, and a whole rinse block labelled with the previous run's code).
- **Copy raw readings, never the calculated block.** Some calculated cells in her sheet have values typed over the formula, so they disagree with the raw reading they came from.
- **Blank, never 0**, for a measurement that wasn't taken.
- **Use the measured feed.** The nominal feed goes in `setups.csv`; the real feed concentration is the t = 0 diluate sample.
- **Tares change between runs**, so take them from that run's own header block.
- **Different starting concentrate** (a different salt or strength) makes a run not comparable with the rest. Record it in `conc_start_salt` / `conc_start_g_l` and consider `include = false`.
