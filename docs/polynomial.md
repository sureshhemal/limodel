# The polynomial

The equation the project fits, in short. Every step, every equation and every number behind it is
in the [plan for building the model](plan-for-building-the-model.md); see
[data-format.md](data-format.md) for where the raw numbers come from.

## What is fitted

Permselectivity `P`, for the GO-10 membrane, from the two settings chosen at the bench:

| Symbol | Meaning | Unit | Levels run so far |
|---|---|---|---|
| `P` | permselectivity, lithium over magnesium | — | the output |
| `i` | current density | mA/cm² | 3, 6, 12, 24 |
| `R` | Mg/Li feed ratio, by moles | mol/mol | 1.43, 2.86, 5.71, 11.4, 17.1 (mass ratios 5, 10, 20, 40, 60) |

Both inputs are rescaled to run from −1 to +1 over the tested range: `x₁` from `i` or `ln i` (both
are tried), `x₂` from `ln R`.

## What P is

```
        n_Li / n_Mg
P = ─────────────────
        c̄_Li / c̄_Mg
```

`n` is the moles of each metal the concentrate gained over the run; `c̄` is each metal's log-mean
concentration in the diluate, between its first and last samples. The top is the Li/Mg ratio that
crossed, the bottom the Li/Mg ratio the membrane was offered. **P = 1 means no preference**; above
1, lithium is favoured. This follows the lab's workbook (column BI).

## The candidates

A fixed ladder, each rung adding one term to the one below:

| Model | Equation |
|---|---|
| M0 | `ŷ = b₀` |
| M1 | `ŷ = b₀ + b₂·x₂` |
| M2 | `ŷ = b₀ + b₂·x₂ + b₁·x₁` |
| M3 | `ŷ = b₀ + b₂·x₂ + b₁·x₁ + b₃·x₁²` |
| M4 | `ŷ = b₀ + b₂·x₂ + b₁·x₁ + b₃·x₁² + b₄·x₂²` |

`ŷ` is `P` or `ln P`. The ratio comes first because its effect is certain from the chemistry: more
magnesium competes harder for the current. There is no `x₁·x₂` term: the runs form a cross (current
density varied at ratio 5, the ratio varied at 12 mA/cm²), which cannot estimate it.

**Choosing:** climb the ladder while the term just added is significant (partial F, p < 0.05),
every coefficient is significant and the lack-of-fit test passes; then check that the model reached
also has the lowest AICc and the lowest leave-one-out error.

## The current result

On the 12 GO-10 runs in the lab's workbook, the ratio model on the log scale is chosen:

```
ln P̂ = 0.900 − 0.449·x₂        which is        P̂ = 4.38 · R^−0.36
```

P falls by about 22 % each time the ratio doubles. Current density does not appear, but that means
*not estimable yet*, not *no effect*: the current-density arm is thin and the repeat runs scatter
widely (pure error 1.39).

## Recovery and voltage

- **Lithium recovery** is modelled the same way and reported beside the most selective setup, with
  no limit on it. It follows from P and the ratio.
- **Stack voltage** has no model yet. The 20 V limit, the most the stack can hold, is checked against
  the measured runs, so only current densities that were actually run can be recommended.

## How it is checked: every run, no test set

There is **no train/test split**. Every usable run goes into the fit, and the error comes from
**leave-one-out cross-validation**: fit on all runs but one, predict the one left out, repeat until
each run has been the left-out one exactly once.

With twelve runs a hold-out set measures nothing. A 75/25 split would train on nine runs and report
an error computed from three; move one run between the piles and that error moves with it.
Leave-one-out spends no data and gives one honest out-of-sample error per run.

A real test comes from new runs: their predictions are written down and dated before the lab
results exist, then compared when they arrive (Step 9 of the plan).
