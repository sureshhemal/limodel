"""Workbook convention, model convention, and the same thing done by weight.

Prints one table per run so the three can be read side by side. Throwaway: the real
calculator lives in the analyzer once step 1 is built.
"""

from limodel.analyzer.journal import Journal
from limodel.analyzer.preprocess.preprocessor import Preprocessor
from limodel.data_loader import DataLoader

LI, MG = 6.94, 24.305
RUNS = ("AE", "AG")

loaded = {run.run_code: run for run in Preprocessor(Journal()).run(DataLoader().load())}
kept = {}


def tare(run, tank):
    return {"conc": run.tare_conc_g, "dil": run.tare_dil_g}[tank]


def ends(run, tank):
    readings = [r for r in run.tank_readings
                if r.tank == tank and r.sample and r.sample.li_mg_l is not None]
    readings.sort(key=lambda r: r.minute)
    return readings[0], readings[-1]


def litres(run, reading):
    return (reading.weight_g - tare(run, reading.tank)) / 1000.0


for code in RUNS:
    run = loaded[code]
    conc_start, conc_end = ends(run, "conc")
    dil_start, _ = ends(run, "dil")
    v_start, v_end = litres(run, conc_start), litres(run, conc_end)
    v_dil = litres(run, dil_start)

    li_mg = conc_end.sample.li_mg_l * v_end - conc_start.sample.li_mg_l * v_start
    mg_mg = conc_end.sample.mg_mg_l * v_end - conc_start.sample.mg_mg_l * v_start
    li_mmol, mg_mmol = li_mg / LI, mg_mg / MG

    # by mass: the share of the weight that crossed
    mass_t_li = li_mg / (li_mg + mg_mg)
    mass_t_mg = mg_mg / (li_mg + mg_mg)
    mass_t_ratio = mass_t_li / mass_t_mg

    # by charge: Mg carries two
    eq_li, eq_mg = li_mmol, 2 * mg_mmol
    charge_t_li = eq_li / (eq_li + eq_mg)
    charge_t_mg = eq_mg / (eq_li + eq_mg)
    charge_t_ratio = charge_t_li / charge_t_mg

    feed_mol = (dil_start.sample.li_mg_l / LI) / (dil_start.sample.mg_mg_l / MG)
    feed_mass = dil_start.sample.li_mg_l / dil_start.sample.mg_mg_l

    workbook_p = mass_t_ratio
    model_p = charge_t_ratio / feed_mol
    weight_p = mass_t_ratio / feed_mass

    recovery = li_mg * 100 / (dil_start.sample.li_mg_l * v_dil)
    kept[code] = (workbook_p, model_p, weight_p, feed_mol, feed_mass, recovery)

    same = "same for all three"
    rows = [
        ("conc volume, start (L)", f"{v_start:.4f}", f"{v_start:.4f}", f"{v_start:.4f}",
         "(weight - tare) / 1000, " + same),
        ("conc volume, end (L)", f"{v_end:.4f}", f"{v_end:.4f}", f"{v_end:.4f}", same),
        ("Li that crossed (mg)", f"{li_mg:.2f}", f"{li_mg:.2f}", f"{li_mg:.2f}", same),
        ("Mg that crossed (mg)", f"{mg_mg:.2f}", f"{mg_mg:.2f}", f"{mg_mg:.2f}", same),
        ("Li that crossed (mmol)", "-", f"{li_mmol:.2f}", "-", "only the charge version needs moles"),
        ("Mg that crossed (mmol)", "-", f"{mg_mmol:.2f}", "-", ""),
        ("Li recovery (%)", f"{recovery:.2f}", f"{recovery:.2f}", f"{recovery:.2f}",
         "IDENTICAL: Li over Li, the molar mass cancels"),
        ("t Li", f"{mass_t_li:.4f}", f"{charge_t_li:.4f}", f"{mass_t_li:.4f}",
         "share of the weight / share of the charge / share of the weight"),
        ("t Mg", f"{mass_t_mg:.4f}", f"{charge_t_mg:.4f}", f"{mass_t_mg:.4f}", ""),
        ("t Li / t Mg", f"{mass_t_ratio:.4f}", f"{charge_t_ratio:.4f}", f"{mass_t_ratio:.4f}",
         "by weight is the same number the workbook gets"),
        ("feed Li / Mg", "not used", f"{feed_mol:.4f}", f"{feed_mass:.4f}",
         "mol/mol for the model, mg/mg by weight"),
        ("P", f"{workbook_p:.4f}", f"{model_p:.4f}", f"{weight_p:.4f}",
         "the answer each convention reports"),
    ]

    print(f"\n  RUN {code}   {run.cem}, "
          f"{run.mg_feed_mg_l / run.li_feed_mg_l:.0f}x more Mg than Li in the feed")
    print(f"  {'':28}{'workbook':>12}{'model':>12}{'by weight':>12}   note")
    print("  " + "-" * 118)
    for label, workbook, model, weight, note in rows:
        mark = "*" if label in ("P", "Li recovery (%)") else " "
        print(f"{mark} {label:27}{workbook:>12}{model:>12}{weight:>12}   {note}")

a, b = (kept[code] for code in RUNS)
print(f"\n  HOW THE THREE COMPARE")
print(f"  {'':26}{RUNS[0]:>12}{RUNS[1]:>12}{'ratio':>10}   reads as")
print("  " + "-" * 118)
print(f"  {'workbook P':24}{a[0]:>12.4f}{b[0]:>12.4f}{a[0] / b[0]:>9.1f}x"
      f"   scale slides with the feed, so these are not comparable")
print(f"  {'model P (charge)':24}{a[1]:>12.4f}{b[1]:>12.4f}{a[1] / b[1]:>9.1f}x"
      f"   no preference is 0.5 at every feed")
print(f"  {'by weight':24}{a[2]:>12.4f}{b[2]:>12.4f}{a[2] / b[2]:>9.1f}x"
      f"   no preference is 1.0 at every feed")
print(f"\n  by weight / model, every run: {a[2] / a[1]:.4f} and {b[2] / b[1]:.4f}"
      f"  <- exactly 2, the charge on Mg")
