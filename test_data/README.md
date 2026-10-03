# test_data

A hundred made-up runs, for exercising the analyzer end to end. **None of this is real.**

Rebuild it with:

```
uv run python scripts/make_test_data.py
```

The seed is fixed, so the same hundred runs come out every time.

Point the app at it:

```
DATA_DIR=test_data MEMBRANES_MODELLED="GO-10,Pristine,PDA/PEI/15CE/BT,PDA-GO10/PEI/BT" \
  uv run limodel analyze
```

## Why it exists

The real runs cannot exercise the modelling. Their settings were never varied together, so no
curve can be fitted and the search can only ever refuse. These runs are a full grid with small
noise, so the fitting has something to find and the whole path can be tested — including the
parts the real data never reaches.

## The files

Same four files as `data/`, plus one more:

| file | rows | |
|---|---|---|
`runs.csv` | 100 | the setup of each run |
`tank_readings.csv` | 5100 | three tanks, every 15 minutes |
`stack_readings.csv` | 1700 | the power log, every 15 minutes |
`samples.csv` | 600 | two samples per tank, at minute 0 and minute 240 |
**`expected.csv`** | 100 | **what the analyzer must say about each run** |

`expected.csv` is the point of the whole thing. Every run was built **backwards**: a recovery,
a permselectivity and the two balance gaps were chosen first, and then the concentrations that
would produce them were worked out and written as the lab results. So it is not a record of
what the code did — it is what the code has to say. The analyzer currently agrees with it to
**2e-6** on permselectivity and **4e-4** on the gaps.

It promises, per run: whether the run reaches the model at all, and if it does its
permselectivity, lithium recovery, highest voltage and both balance gaps.

### The balance gaps are built in on purpose

The books are made to **fail to close**, because gaps of zero would exercise nothing and look
nothing like a real run. Each run is given a gap to hit, and the dilute's end sample is then
written to produce exactly it. That works without disturbing anything else because of which
readings each number uses:

| used by | conc start and end | dilute start | dilute end | rinse |
|---|---|---|---|---|
recovery | yes | yes | | |
permselectivity | yes | yes | | |
balance gap | yes | yes | yes | yes |

The dilute's end sample and the rinse feed **nothing but the gaps**, so they can be pushed
about freely. The gaps across the hundred runs span **-38 % to +44 %**, and about a third are
negative — metal arriving from nowhere, which is what the real runs show too.

A gap wider than the tank can give up is cut back, and the gap written down is then the one
the readings really produce rather than the one that was asked for.

## What is in the hundred

**A full grid.** 4 membranes x 5 current densities x 4 feed ratios = 80 runs, every cell
filled. Then 20 more that repeat settings already run, 5 per membrane, so there is a bench
scatter to judge a fit against.

| | |
|---|---|
membranes | GO-10, Pristine, PDA/PEI/15CE/BT, PDA-GO10/PEI/BT |
current density | 4.5, 7.5, 13.67, 20.0, 25.67 mA/cm2 |
feed, as Mg over Li by weight | 2.5, 5, 10, 20 |
feed, as the model sees it | 0.71, 1.43, 2.86, 5.71 mol/mol |

Because both settings move together, the design is a grid rather than a cross, and the fitting
can do things the real data will not let it do.

## The answers hidden in it

The runs were drawn around a known shape, written as a hump in **logged** current density so
it is the shape the fitting looks for:

| | |
|---|---|
best current density for permselectivity | **12.0 mA/cm2** |
best current density for recovery | **16.0 mA/cm2** |
best feed ratio | the lowest, **0.714 mol/mol** |

A correct search has to land near those. It currently answers **11.7 mA/cm2 at 0.71 mol/mol**
for GO-10 — the permselectivity optimum found to within 2.5 %, and the feed ratio exactly.

Each membrane is the same shape scaled down: GO-10 at full strength, PDA/PEI/15CE/BT at 0.78,
PDA-GO10/PEI/BT at 0.71, Pristine at 0.42. **Pristine is deliberately too weak to clear the
35 % recovery floor**, so it fits cleanly and is then refused by the gate — which is a path
worth testing on its own.

## The faults planted on purpose

Eleven runs never reach the model, and ten readings are cleared. All of them are deliberate,
and all of them are named in the `notes` column of `runs.csv`.

| run | what is wrong | what should happen |
|---|---|---|
T003 T019 T044 T072 T088 T095 | marked not for use | dropped |
T011 T027 T053 T079 T091 | the lab has not answered for the end sample | dropped |
T007 T066 | a weight nothing like the rest of its series | that one weight cleared |
T013 | a pH outside anything a solution reaches | cleared |
T021 | a pH that moved too fast | cleared |
T029 | a temperature the room cannot reach | cleared |
T034 | a temperature that moved too fast | cleared |
T042 | a conductivity jump that comes back | cleared |
T048 | the two voltmeters disagreeing | cleared |
T055 | the two ammeters out of proportion | cleared |
T061 | a supply current nothing like the rest | cleared |

Every planted fault sits at a minute that is **never sampled**, so clearing it cannot change
the answers in `expected.csv`.

So a correct run of the analyzer over this directory gives: **100 loaded, 89 after
preprocessing, 89 calculated, 21 journal entries — 11 runs dropped and 10 readings skipped.**
