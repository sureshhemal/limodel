# The polynomial

The equation the project fits. See the [README](../README.md) for the project as a whole,
and [data-format.md](data-format.md) for where the numbers come from.

## What we are fitting

A second-order polynomial that predicts permselectivity from the two settings that can be
dialled on the rig:

```
P̂ = b₀ + b₁·J + b₂·R + b₃·J² + b₄·R² + b₅·J·R
```

Six coefficients: an intercept, two linear terms, two curvature terms, and one interaction
term. The interaction is the term that says whether the best current depends on how much Mg
is in the feed.

## The symbols

| Symbol | Meaning | Unit | Levels she ran |
|---|---|---|---|
| `P` | Permselectivity, Li over Mg | — | the outcome |
| `J` | Current density | mA/cm² | 3, 6, 12, 24 |
| `R` | Mg/Li ratio in the diluate | mol/mol | 5, 10, 20, 40, 60 |

`P` above 1 means the membrane favours Li over Mg relative to what the feed offered:

```
        t_Li / t_Mg
P = ─────────────────        t_Li = n_Li / (n_Li + 2·n_Mg)
        c_Li / c_Mg          t_Mg = 2·n_Mg / (n_Li + 2·n_Mg)
```

where `n` is the moles each ion added to the concentrate over the run, and `c` is the molar
concentration measured in the diluate at minute 0.

The membrane is not a polynomial variable — it is a category (GO-10, pristine, PDA/PEI/15CE,
PDA/GO10/PEI). It enters either as a 0/1 indicator or by fitting the equation once per
membrane.

## Three polynomials, not one

The question is *the best P subject to limits*, so every quantity a limit is placed on needs
its own prediction. Same six-term shape, same `J` and `R`, different outcome column:

| Fitted | Role | Limit |
|---|---|---|
| `P` | what we maximise | — |
| Li recovery (%) | gate | must reach 35 % |
| Voltage (V) | gate | must stay at or below 20 V |

## The data behind it

One row per run: `J` and `R` as the x columns, the three outcomes as the y columns. 21 runs
exist; 17 have lab results so far. `calc.py` builds this table from the four CSV files.
