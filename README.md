# limodel

A model for finding the best electrodialysis setup for separating lithium from magnesium.

**The question:** for a feed with a given Mg/Li ratio, which current density and which membrane give the best Li selectivity?

**What counts as "best":**

- **Maximise** permselectivity `P = (t_Li / t_Mg) / (c_Li / c_Mg)`
  - `t` is each ion's share of the charge carried: `t_Li = n_Li / (n_Li + 2·n_Mg)`, using moles gained by the concentrate
  - `c` is the feed concentration at the start of the run (diluate, t = 0), in mol/m³
- **Safety gate:** starting supply voltage ≤ 20 V (membranes break above it)
- **Usefulness gate:** Li recovery at the end of the run ≥ 35% (provisional)

The approach follows §2.5 of the GO-10 manuscript: a second-order polynomial surrogate model, with XGBoost fitted only as a comparison.

## Setup and running

### 1. Install uv (once per computer)

[uv](https://docs.astral.sh/uv/) manages Python itself, the project's virtual environment (`.venv/`) and its packages. It works like Composer for PHP.

- **macOS:** `brew install uv`
- **Windows (PowerShell):** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

Check it with `uv --version`.

### 2. Get the project

Clone or copy the project folder, then open a terminal in it:

```
cd Li-Research
```

### 3. Choose the Python version (recommended)

```
uv python pin 3.13
```

This writes `.python-version`. uv downloads Python 3.13 for this project if it isn't installed, and it doesn't affect any other Python on the computer. 3.13 is safer than the newest release for the scientific packages.

### 4. Install everything

```
uv sync
```

This creates `.venv/`, installs the dependencies and dev tools, installs `limodel` from `src/`, and writes `uv.lock` with the exact versions. Run it again after pulling changes, or whenever `pyproject.toml` changes.

### 5. Run

```
uv run limodel            # shows the help screen
uv run limodel --help     # same
```

`uv run` always uses the project's `.venv`, so there's no need to activate it.

> No commands are defined yet. Each one is added as an `@app.command()` function in `src/limodel/cli/main.py` once its module is written.

### 6. Tests and notebooks

```
uv run pytest            # run the tests in tests/
uv run jupyter lab       # open notebooks/ for exploration
```

### Everyday workflow

1. Add or correct data in `data/`: a row in `setups.csv`, plus `readings/<CODE>_readings.csv` and `samples/<CODE>_samples.csv`.
2. Run the model from the terminal (commands to be added).
3. Open `output/` for the charts and tables.

### Adding packages

```
uv add xgboost           # a dependency the app needs
uv add --dev ruff        # a tool only for development
```

Both update `pyproject.toml` and `uv.lock`. Commit those two files.

### PyCharm

- *Settings → Project → Python Interpreter* → select the project's `.venv/bin/python` (created by `uv sync`)
- Right-click `src` → *Mark Directory as* → *Sources Root*

## Project structure

```
Li-Research/
├── .gitignore                  ← ignores .venv, output/, .env, .idea, Excel lock files
├── data/
│   ├── setups.csv              ← one row per experiment
│   ├── readings/               ← <CODE>_readings.csv go here
│   └── samples/                ← <CODE>_samples.csv go here
├── output/                     ← generated reports (git-ignored)
├── notebooks/                  ← exploration
├── src/limodel/
│   ├── __init__.py
│   ├── schema.py               ← column definitions
│   ├── checks.py               ← data problems → issues list
│   ├── calc.py                 ← raw → flux, t, P, recovery, start voltage
│   ├── fit.py                  ← polynomial fits + CV
│   ├── best_setup.py           ← gates + search for highest P
│   ├── sources/
│   │   ├── base.py             ← the data-source contract
│   │   └── csv_source.py       ← reads data/
│   └── cli/                    ← terminal-only, replaced in phase 2
│       ├── main.py             ← the terminal app and its commands
│       ├── charts.py           ← curve data → PNG
│       └── report.py           ← writes output/
└── tests/
    ├── test_calc.py
    └── test_checks.py
```

## How the pieces fit

```
data/*.csv → sources → checks → calc → fit → best_setup → cli (charts, report) → output/
```

### `data/`: raw values only

The CSV files hold only what was set, measured at the rig, or reported by the lab. Every derived number is calculated by the code. To correct a value, edit the CSV and run again; everything downstream updates.

| File | One row per | Contents | Recorded |
|---|---|---|---|
| `setups.csv` | experiment | Membranes, feed, starting concentrate, rinse, flow, area, cell pairs, tare weights, `include`, `notes` | before the run |
| `readings/<CODE>_readings.csv` | time mark (minute) | Power log (supply and multimeter V/I); tank conductivity, pH, temperature, weight; IDs of samples taken | during the run |
| `samples/<CODE>_samples.csv` | sample | Li, Mg, Na, K, Ca (ICP) and TOC, by `sample_id` | by the lab, later |

`setups.code` names the other two files (e.g. `AE` → `AE_readings.csv`, `AE_samples.csv`). A sample's time and tank are recorded only in the readings file, through `conc_sample_id`, `dil_sample_id` and `rinse_sample_id`.

Rules:

- Blank means not measured. Never enter 0 for a missing value.
- No calculated columns.
- Units go in column names only; cells hold plain numbers.
- Same headers, same order, in every file.
- Membrane names and sample IDs are spelled exactly the same everywhere.
- Runs that shouldn't be used get `include = false` and a reason in `notes`. They are never deleted.

### `setups.csv` columns

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

### `src/limodel/`: the science

Pure Python. It never prints, saves files or draws charts. Every function returns plain data (numbers, pandas tables, dataclasses), so the same code can later serve a Django API and a Vue frontend unchanged.

| Module | Job |
|---|---|
| `schema.py` | The single definition of every column: name, type, unit, required. Used for loading and for checks, and later mirrored by the database tables. |
| `sources/base.py` | The contract every data source provides: `get_setups()`, `get_readings(code)`, `get_samples(code)`. |
| `sources/csv_source.py` | Implements the contract by reading `data/`. A PostgreSQL source replaces it in phase 2 without changing anything else. |
| `checks.py` | Finds data problems: missing files, unmatched or duplicate sample IDs, blanks where values are required, out-of-range values, samples still waiting on lab results, mass-balance errors. |
| `calc.py` | Turns raw readings into physical quantities (volume = (weight − tare)/1000, moles, charge, current density), then one summary row per run: Li and Mg flux, t_Li, t_Mg, P, Li recovery, starting voltage. |
| `fit.py` | Fits the second-order polynomials for P, Li recovery and starting voltage (inputs: current density and Mg/Li ratio; one model per membrane). Reports R², RMSE and cross-validation error. |
| `best_setup.py` | For each membrane and Mg/Li ratio, scans current density within the tested range, drops settings that break the voltage or recovery gates, and returns the one with the highest P, together with the curve points. |

### `src/limodel/cli/`: the terminal interface

The only part that prints, draws or writes files. It is replaced by Django + Vue in phase 2.

`main.py` defines the `limodel` terminal app. Running `limodel` with no command shows its help. No commands are defined yet; they are added as the modules they depend on are written.

`charts.py` turns curve data into PNGs with matplotlib; `report.py` writes the `output/` folder.

### `tests/`

- `test_calc.py`: the calculated P, t_Li and recovery for a known run must match the values in her spreadsheet.
- `test_checks.py`: known data problems must be detected.

## Phases

1. **Phase 1 (now):** pure Python, run from the terminal, reading CSV files on her computer.
2. **Phase 2:** Django (API) + Vue frontend, with data in hosted PostgreSQL (e.g. Neon). `src/limodel/` carries over unchanged; `cli/` is replaced and `csv_source.py` gets a database counterpart.
