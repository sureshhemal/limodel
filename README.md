# limodel

[![tests](https://github.com/sureshhemal/limodel/actions/workflows/tests.yml/badge.svg)](https://github.com/sureshhemal/limodel/actions/workflows/tests.yml)

A model for finding the best electrodialysis setup for separating lithium from magnesium.

**The question:** for a feed with a given Mg/Li ratio, which current density and which membrane give the best Li selectivity?

**What counts as "best":**

- **Maximise** permselectivity `P = (t_Li / t_Mg) / (c_Li / c_Mg)`
  - `t` is each ion's share of the charge carried: `t_Li = n_Li / (n_Li + 2·n_Mg)`, using moles gained by the concentrate
  - `c` is the feed concentration at the start of the run (diluate, t = 0), in mol/m³
- **Safety gate:** starting supply voltage ≤ 20 V (membranes break above it)
- **Usefulness gate:** Li recovery at the end of the run ≥ 35% (provisional)

The approach follows §2.5 of the GO-10 manuscript: a second-order polynomial surrogate model, with XGBoost fitted only as a comparison.

**Where it is now:** the data is converted from her workbook, `limodel verify` compares it cell by cell with that workbook, and `limodel check` reports everything wrong with it. The calculations (`calc`, `fit`, `best_setup`) are still to be written.

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
uv run limodel --help     # the commands
uv run limodel convert    # rebuild the data files from her workbook
uv run limodel check      # list everything wrong with the data
uv run limodel verify     # compare every value with her workbook
```

`uv run` always uses the project's `.venv`, so there's no need to activate it.

`check` never fails, even on unreadable data — that is the point of it. The commands that compute results refuse invalid data instead; see [Everyday workflow](#everyday-workflow).

> Only `convert`, `check` and `verify` exist so far. Each new command is an `@app.command()` function in `src/limodel/cli/main.py`.

### 6. Tests and notebooks

```
uv run pytest            # run the tests in tests/
uv run pytest -v         # one line per test
uv run jupyter lab       # open notebooks/ for exploration
```

The tests also run on every pull request, through `.github/workflows/tests.yml`.

### Everyday workflow

1. **`uv run limodel convert`** — rebuilds the four files in `data/` from her workbook. It asks first, because it replaces them.
2. **`uv run limodel check`** — lists every problem in the data. It never fails, so it can be run at any time.
3. Fix those in her workbook and convert again.
4. **`uv run limodel verify`** — confirms the files still hold exactly what the workbook holds.
5. Repeat until `check` reports nothing.
6. Run the model (commands still to be written) and open `output/` for the charts and tables.

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
│   ├── runs.csv                ← one row per experiment
│   ├── stack_readings.csv      ← power log for every run
│   ├── tank_readings.csv       ← conductivity, pH, temp, weight per tank
│   └── samples.csv             ← lab results for every sample
├── docs/
│   └── data-format.md          ← column definitions and how to create the CSVs
├── output/                     ← generated reports (git-ignored)
├── notebooks/                  ← exploration
├── src/limodel/
│   ├── config.py               ← settings, read once from .env
│   ├── data_loader.py          ← the front door: the only thing the app depends on
│   ├── sources/
│   │   └── csv_source.py       ← reads data/, validated against the schema
│   ├── schema/                 ← one pandera model per file: what a CSV must look like
│   │   ├── run.py
│   │   ├── stack_reading.py
│   │   ├── tank_reading.py
│   │   └── sample.py
│   ├── models/                 ← one pydantic model per thing: what the app works with
│   │   ├── run.py              ← a run, with its readings inside it
│   │   ├── stack_reading.py
│   │   ├── tank_reading.py     ← carries the sample drawn from it, if there was one
│   │   └── sample.py
│   ├── checks.py               ← finds every data problem, without raising
│   ├── workbook/               ← her Excel workbook, in and out
│   │   ├── cells.py            ← where everything sits in her sheets
│   │   ├── convert.py          ← the workbook → the four CSV files
│   │   └── compare.py          ← the four CSV files → every difference from the workbook
│   ├── calc.py                 ← raw → flux, t, P, recovery, start voltage
│   ├── fit.py                  ← polynomial fits + CV
│   ├── best_setup.py           ← gates + search for highest P
│   └── cli/                    ← terminal-only, replaced in phase 2
│       ├── main.py             ← the terminal app and its commands
│       ├── charts.py           ← curve data → PNG
│       └── report.py           ← writes output/
└── tests/
    ├── conftest.py             ← fixtures
    ├── fixtures/*.csv          ← small test data, independent of her workbook
    ├── commands/                ← one file per command
    ├── sources/                ← loader, source and checks tests
    └── test_calc.py
```

## How the pieces fit

```
                 ┌─ raw_tables() ─► checks ───────────────────────► `limodel check`
data/*.csv ─► DataLoader
                 └─ load() ─► list[Run] ─► calc ─► fit ─► best_setup ─► cli ─► output/
```

Everything reads its data through `DataLoader`, which picks a source from `config.DATA_SOURCE`.

- **`load()`** validates every table against its schema and returns the runs as objects, so the calculations can never run on bad data.
- **`raw_tables()`** hands the tables over unchecked, which is how `check` reports problems instead of refusing to open the files.

The objects are the shape the science reads:

```python
run = DataLoader().load()[0]

run.id                              # "AE"
run.cem, run.cell_pairs             # "GO-10", 10
run.stack_readings[0].supply_voltage_v
run.tank_readings[0].weight_g       # the tank at that minute
run.tank_readings[0].sample.li_mg_l # the sample drawn from it, or None
```

A sample belongs to the tank reading it was drawn from, so weight and concentration — the two halves of "how many moles" — sit on the same object. Every object also has a derived `id` (`AE`, `AE:60`, `AE:conc:60`, `AE1`) and its foreign keys (`run_id`, `tank_id`), computed from the natural keys rather than stored.

`calc` turns those objects into **one summary row per run**, and from there it is pandas again: a 21-row table is what `fit` hands to scikit-learn.

### `data/`: raw values only, and not in git

The CSV files hold only what was set, measured at the rig, or reported by the lab. Every derived number is calculated by the code. To correct a value, fix her workbook and re-run the converter; everything downstream updates.

| File | One row per | Contents | Recorded |
|---|---|---|---|
| `runs.csv` | experiment | How the run was set up | before the run |
| `stack_readings.csv` | time mark of a run | The power log | during the run |
| `tank_readings.csv` | tank at a time mark | Conductivity, pH, temperature, weight | during the run |
| `samples.csv` | sample | Li, Mg, Na, K, Ca (ICP) and TOC | by the lab, later |

The files themselves are **git-ignored**: they are her experimental data, regenerated from her workbook with `limodel convert`, so a clone starts with an empty `data/` folder.

**[docs/data-format.md](docs/data-format.md) has the full column definitions, the rules, and step-by-step instructions for turning one of her spreadsheet sheets into these four files.**

## The code

### `src/limodel/`: the science

Pure Python. It never prints, saves files or draws charts. Every function returns plain data (numbers, pandas tables, dataclasses), so the same code can later serve a Django API and a Vue frontend unchanged.

| Module | Job |
|---|---|
| `config.py` | Settings, read once from the environment and `.env`: where the data comes from, where it lives, and where her workbook is. |
| `data_loader.py` | The front door. Everything else asks it for tables and never learns where they came from. |
| `sources/csv_source.py` | Reads the four CSV files, caches each one, and names the file when it is missing. |
| `schema/` | One [pandera](https://pandera.readthedocs.io) model per file: types, required values, ranges, uniqueness, no unexpected columns. Every table is validated as it is handed out. |
| `models/` | One [pydantic](https://docs.pydantic.dev) model per thing — `Run`, `StackReading`, `TankReading`, `Sample` — with the nesting, the computed ids and the foreign keys. This is what `load()` returns. |
| `checks.py` | Finds every problem in one pass without raising, and explains each in plain words. Still to add: cross-table rules such as mass balance and samples still waiting on the lab. |
| `workbook/` | Her Excel workbook: `convert.py` builds the four CSV files from it, copying every value as recorded and reporting rather than correcting; `compare.py` walks the sheets and reports every value the CSV files do not match, including a reading that never arrived. `cells.py` holds the sheet layout both of them read. |
| `calc.py` | Turns raw readings into physical quantities (volume = (weight − tare)/1000, moles, charge, current density), then one summary row per run: Li and Mg flux, t_Li, t_Mg, P, Li recovery, starting voltage. |
| `fit.py` | Fits the second-order polynomials for P, Li recovery and starting voltage (inputs: current density and Mg/Li ratio; one model per membrane). Reports R², RMSE and cross-validation error. |
| `best_setup.py` | For each membrane and Mg/Li ratio, scans current density within the tested range, drops settings that break the voltage or recovery gates, and returns the one with the highest P, together with the curve points. |

### `src/limodel/cli/`: the terminal interface

The only part that prints, draws or writes files. It is replaced by Django + Vue in phase 2.

`main.py` defines the `limodel` terminal app and its commands. So far there are three:

| Command | Does |
|---|---|
| `limodel convert` | Rebuilds the four data files from her workbook. Asks before replacing them, unless `--force` |
| `limodel check` | Lists every problem in the data, and never fails |
| `limodel verify` | Compares every value with the cell it came from in her workbook, named by `WORKBOOK` in `.env` |

`summary`, `fit`, `best` and `report` follow as the modules they depend on are written.

`charts.py` turns curve data into PNGs with matplotlib; `report.py` writes the `output/` folder.

### `tests/`

Fixture CSV files under `tests/fixtures/` stand in for her data, so the tests do not depend on her workbook.

| File | Covers |
|---|---|
| `sources/test_csv_source.py` | loading, types, caching, and every kind of rejection |
| `sources/test_data_loader.py` | choosing the source, and the shape of what `load()` returns |
| `sources/test_find_problems.py` | each kind of problem, reported once, with the right run and column |
| `commands/test_check.py` | the command prints the list and exits 0 even when the data is unreadable |
| `commands/test_convert.py` | the four files written from a workbook, a value copied as recorded, a warning instead of a correction, and the question before replacing files |
| `commands/test_verify.py` | a workbook built in the test, matching and mismatching, and a missing `WORKBOOK` |
| `test_calc.py` | still to write: the calculated P, t_Li and recovery for a known run must match her spreadsheet |

## Phases

1. **Phase 1 (now):** pure Python, run from the terminal, reading CSV files on her computer.
2. **Phase 2:** Django (API) + Vue frontend. `src/limodel/` carries over unchanged; `cli/` is replaced and the data source can change behind `DataLoader`.
