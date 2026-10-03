"""Reports the modelling: what it could use, and what it found."""

import statistics

from limodel.analyzer.calculate.constants import LI_G_PER_MOL

import typer

from limodel import config
from limodel.analyzer.calculate.quantities.charge_per_lithium_offered import ChargePerLithiumOffered

from limodel.analyzer import Action, Analyzer, Journal
from limodel.analyzer.model.best_setup_under_the_gates import (HIGHEST_VOLTAGE, LI_RECOVERY,
                                                               PERMSELECTIVITY)
from limodel.analyzer.model.design_points import DesignPoints
from limodel.analyzer.model.surrogate import Surrogate


class Analyze:
    """Prints the analysis: what was left out, every run calculated, then the fits.

    The exclusions come first on purpose. A reader who sees only the answer should still
    know how many runs it came from, and which of those runs are thin.
    """

    # Each column of the run table: heading, the field it reads, its decimals. A column with
    # no decimals holds words and sits to the left; the numbers line up right. The widths are
    # measured off the values printed, since a membrane name can be twice its heading.
    COLUMNS = (("run", "run_code", None),
               ("membrane", "cem", None),
               ("mA/cm2", "current_density_ma_cm2", 2),
               ("Mg/Li", "feed_mg_li_ratio", 2),
               ("perm", "permselectivity", 3),
               ("recovery %", "li_recovery_pct", 1),
               ("volts", "highest_voltage_v", 1),
               ("mAh/cm2", "charge_passed_mah_cm2", 1),
               ("Li gap %", "li_balance_gap_pct", 1),
               ("Mg gap %", "mg_balance_gap_pct", 1))

    # What each column of the table is. Keyed by the field, so a heading renamed in COLUMNS
    # cannot leave its own explanation behind. The run code and the membrane need none.
    COLUMN_MEANINGS = {
        "current_density_ma_cm2": "a setting: the current that was measured, per cm2 of membrane",
        "feed_mg_li_ratio": "a setting: magnesium per lithium in the feed, in mol/mol",
        "permselectivity": "what the model maximises: how far lithium was preferred over "
                           "magnesium. 0.5 is no preference at all",
        "li_recovery_pct": "a gate: the share of the feed's lithium that crossed. "
                           "{floor:g} % or more passes",
        "highest_voltage_v": "a gate: the highest the supply reached. "
                             "{ceiling:g} V or less passes",
        "charge_passed_mah_cm2": "not modelled: how much charge went through, per cm2. "
                                 "Near enough equal on every run, by design",
        "li_balance_gap_pct": "a check, not a result: the lithium the readings cannot "
                              "account for",
        "mg_balance_gap_pct": "the same for magnesium. A large or a negative gap means that "
                              "row is thin",
    }

    # Worked out for the reader to judge a run by, never fitted. A run missing one is still
    # modelled, so the report names it at the end rather than dropping it.
    DIAGNOSTIC_NAMES = ("highest_voltage_v", "charge_passed_mah_cm2", "energy_per_mol_li_wh",
                        "li_balance_gap_pct", "mg_balance_gap_pct")

    OUTCOME_LABELS = {PERMSELECTIVITY: "permselectivity", LI_RECOVERY: "recovery %",
                      HIGHEST_VOLTAGE: "volts"}

    # Plain words for the report. The article is part of the label so the sentences read.
    SETTING_LABELS = {"current_density_ma_cm2": "current density",
                      "feed_mg_li_ratio": "the feed ratio",
                      "charge_per_li_offered": "how hard it was pushed"}

    # Magnesium weighs this much more than lithium per ion, which turns a ratio in moles
    # into the grammes a bottle is actually made up with.
    MG_PER_LI_BY_WEIGHT = 24.305 / 6.94

    MISSING = "-"      # a number that could not be worked out; "None" in a table is noise
    LABEL_WIDTH = 17   # the widest label under a membrane, so those lines line up
    COLUMN_GAP = "  "  # two spaces between columns, wide enough to read as a break
    ERROR_PLACES = 3   # decimals on an error, and the resolution it is judged at

    def __init__(self, loader, journal: Journal):
        self.loader = loader
        self.journal = journal

    def run(self):
        """Run the modelling, print what it worked from and what it found, and hand it back."""
        analysis = Analyzer(self.loader, self.journal).analyze()

        for line in self._find_report(analysis):
            typer.echo(line)

        return analysis

    def _find_report(self, analysis):
        """Every line of the report, in the order a reader needs them."""
        return self._find_sections_apart([
            self._find_journal_lines(),
            [f"using {len(analysis.used)} of {self._find_runs_loaded(analysis)} runs"],
            self._find_result_lines(analysis.results),
            self._find_legend_lines(analysis.results),
            self._find_model_lines(analysis.models, analysis.results),
            self._find_thin_lines(analysis.results)])

    def _find_journal_lines(self):
        """One line per run dropped and per reading skipped, with the reason."""
        return [f"  {entry.action!s:<9}{self._find_type(entry):<9}{entry.id:<15}{entry.reason}"
                for entry in self._find_entries_in_order(self.journal.entries)]

    def _find_result_lines(self, results):
        """The table: a heading, then the numbers of every run that was calculated."""
        if not results:
            return []

        rows = [[heading for heading, _, _ in self.COLUMNS],
                *[self._find_result_cells(result) for result in results]]
        widths = self._find_column_widths(rows)

        return [self._find_table_row(cells, widths) for cells in rows]

    def _find_legend_lines(self, results):
        """What each column holds, so the table can be read without reaching for the docs."""
        if not results:
            return []

        explained = [(heading, name) for heading, name, _ in self.COLUMNS
                     if name in self.COLUMN_MEANINGS]
        width = max(len(heading) for heading, _ in explained)

        # The gates are a setting, so the legend quotes the ones actually in force.
        limits = {"floor": config.RECOVERY_FLOOR_PCT, "ceiling": config.VOLTAGE_CEILING_V}

        return ["what the columns mean",
                *[f"  {heading:<{width}}{self.COLUMN_GAP}"
                  f"{self.COLUMN_MEANINGS[name].format(**limits)}"
                  for heading, name in explained]]

    def _find_result_cells(self, result):
        """One calculated run, column by column."""
        return [self._find_number(getattr(result, name, None), places)
                for _, name, places in self.COLUMNS]

    def _find_table_row(self, cells, widths):
        """One line of the table, each cell in the width and the alignment of its column."""
        return self.COLUMN_GAP.join(
            f"{cell:<{width}}" if places is None else f"{cell:>{width}}"
            for cell, width, (_, _, places) in zip(cells, widths, self.COLUMNS)).rstrip()

    def _find_model_lines(self, models, results):
        """A block per membrane: the settings fitted in, the terms, the error, the setup."""
        # The fitting's own grouping, so the report names the rows the fit was really made on.
        rows_by_cem = Surrogate(self.journal).find_membranes(results)

        return self._find_sections_apart(
            [self._find_membrane_lines(models, cem, rows_by_cem.get(cem, []))
             for cem in self._find_membranes_in_order(models)])

    def _find_membrane_lines(self, models, cem, rows):
        """One membrane's block, from its name down to the setup it allows."""
        fits = models.fits.get(cem, {})

        return [cem,
                *self._find_fitted_setting_lines(fits, rows),
                *self._find_outcome_lines(fits),
                *self._find_setup_lines(models, cem, rows)]

    def _find_fitted_setting_lines(self, fits, rows):
        """Which settings the fit moved over, so a fit in one is never read as a fit in two."""
        if not fits:
            return []

        points = DesignPoints(rows)
        kept = points.find_kept_settings()

        if not kept:
            return []

        held = points.find_dropped_settings() or ()
        said = self._find_setting_words(kept)

        if held:
            said += (f", with {self._find_setting_words(held)} held at one value across "
                     f"these runs and never tested")

        return [self._find_labelled("fitted in", said)]

    def _find_outcome_lines(self, fits):
        """Two lines per fitted outcome: the terms it kept, and what its error is worth."""
        lines = []

        for name, fit in fits.items():
            lines.append(self._find_labelled(self.OUTCOME_LABELS.get(name, name),
                                             self._find_equation(fit)))
            lines.append(self._find_labelled("", self._find_judgement(fit)))

        return lines

    def _find_setup_lines(self, models, cem, rows=()):
        """The setup this membrane allows, or the reason it has none."""
        if cem in models.not_fitted:
            return [self._find_labelled("not fitted", models.not_fitted[cem])]

        setup = models.best_setups.get(cem)

        if setup is None:
            return []

        settings = setup.find_settings()

        if settings is None:
            return [self._find_labelled("no best setup", setup.find_refusal()),
                    *self._find_nearest_lines(setup)]

        return [self._find_labelled("best setup", self._find_setting_words_for(settings)),
                self._find_labelled("", self._find_promise(setup)),
                *self._find_bench_lines(settings, rows)]

    @staticmethod
    def _find_setting_words_for(settings):
        """A setup in the units it was fitted in: the current, the feed, and how hard to push."""
        current_density, feed_ratio, charge_per_li = settings

        return (f"{current_density:.1f} mA/cm2 at a feed of {feed_ratio:.2f} mol/mol, "
                f"to {charge_per_li:.2f} equivalents per lithium")

    def _find_bench_lines(self, settings, rows):
        """The same setup written as instructions, so it can be followed as it reads.

        The block above it is the setting in the units the fitting works in, which is what
        the coefficients beside it are in. This one is the same setting for the person at
        the rig: a dial to turn, a feed to mix, and a time to stop.
        """
        current_density, feed_ratio, charge_per_li = settings
        area = self._find_usual(rows, "area_cm2")
        li_feed = self._find_usual(rows, "li_feed_mg_l")
        by_weight = feed_ratio * self.MG_PER_LI_BY_WEIGHT
        said = [f"mix the feed with {by_weight:.2f} g of magnesium for every 1 g of lithium"]

        if area is not None:
            said.insert(0, f"set the supply to {current_density * area:.0f} mA, "
                           f"through the {area:g} cm2 membrane")

        if li_feed is not None:
            said.append(f"so at {li_feed:g} mg/L of lithium, use "
                        f"{li_feed * by_weight:.0f} mg/L of magnesium")

        hours = self._find_hours(charge_per_li, current_density, area, li_feed, rows)

        offered = self._find_middling(rows, "li_offered_mmol")

        if hours is not None and offered is not None:
            # How long depends on how much lithium goes in, which is the experimenter's choice
            # and not the model's, so the amount it was worked out for is said plainly.
            grammes = offered * LI_G_PER_MOL / 1000

            said.append(f"run it for about {hours:.1f} hours, for a feed tank holding "
                        f"{grammes:.2f} g of lithium")
            said.append(f"twice as much lithium in the tank means twice as long")

        return [self._find_labelled("how to run it", said[0]),
                *[self._find_labelled("", line) for line in said[1:]]]

    @staticmethod
    def _find_hours(charge_per_li, current_density, area, li_feed, rows):
        """How long the run has to go on to reach that charge; None without the setup for it."""
        offered = Analyze._find_middling(rows, "li_offered_mmol")
        pairs = Analyze._find_usual(rows, "cell_pairs")

        if area is None or offered is None or pairs is None:
            return None

        return ChargePerLithiumOffered.find_hours(charge_per_li, offered, pairs,
                                                  current_density * area / 1000)

    @staticmethod
    def _find_middling(rows, field_name):
        """The middle run's value, for a number that cannot be given without assuming one.

        The median rather than the mean, so one run with a tank four times the size cannot
        drag the figure the report quotes.
        """
        found = [getattr(row, field_name, None) for row in rows]
        found = [value for value in found if value is not None]

        return statistics.median(found) if found else None

    @staticmethod
    def _find_usual(rows, field_name):
        """The value these runs were set up with, when they all agree; None when they do not."""
        found = {getattr(row, field_name, None) for row in rows}
        found.discard(None)

        return found.pop() if len(found) == 1 else None

    def _find_nearest_lines(self, setup):
        """The best the runs can offer when no point passes, with what it falls short on.

        A refusal on its own leaves a reader nowhere to go, and the closest setting is what
        says whether the gate was missed narrowly or by a mile.
        """
        settings = setup.find_settings_without_the_gates()
        predictions = setup.find_predictions_without_the_gates()

        if settings is None or predictions is None:
            return []

        return [self._find_labelled("closest anyway", self._find_setting_words_for(settings)),
                self._find_labelled("", self._find_promise(setup, predictions)),
                self._find_labelled("", self._find_shortfall_words(setup))]

    def _find_shortfall_words(self, setup):
        """How far the closest setting misses each gate, so the size of the gap is plain."""
        missed = setup.find_shortfalls(setup.find_best_point_without_the_gates())

        if not missed:
            return "it clears both gates, so the refusal is about the runs, not this setting"

        return "short of the " + " and the ".join(
            f"{gate} by {by:.3g}" for gate, by in missed.items())

    def _find_promise(self, setup, predictions=None):
        """What all three outcomes come to at a setting: the winner's, or ones handed in."""
        predictions = predictions if predictions is not None else setup.find_best_predictions()
        predictions = predictions or {}

        return ", ".join(f"{self.OUTCOME_LABELS.get(name, name)} {value:.3f}"
                         for name, value in predictions.items())

    def _find_thin_lines(self, results):
        """Names every calculated run with a diagnostic missing, so thin numbers show."""
        thin = [result.run_code for result in results
                if any(getattr(result, name, None) is None for name in self.DIAGNOSTIC_NAMES)]

        if not thin:
            return []

        return [f"diagnostics missing on {', '.join(thin)}"]

    def _find_labelled(self, label, text):
        """One line under a membrane: an indent, the label column, then what it says."""
        return f"  {label:<{self.LABEL_WIDTH}}{text}"

    def _find_runs_loaded(self, analysis):
        """How many runs there were before any were dropped."""
        used = {run.run_code for run in analysis.used}

        # A run whose numbers would not come out is dropped after the preprocessing already
        # kept it, so the used ones are left out here rather than counted twice.
        dropped = {entry.id for entry in self.journal.entries
                   if entry.action is Action.DROP and entry.id not in used}

        return len(used) + len(dropped)

    @staticmethod
    def _find_membranes_in_order(models):
        """Every membrane the fitting met, fitted or refused, each named once."""
        return list(dict.fromkeys([*models.fits, *models.not_fitted]))

    @staticmethod
    def _find_equation(fit):
        """The surviving terms with their coefficients, as the fit came out."""
        terms = fit.find_terms_and_coefficients() or ()

        return ", ".join(f"{name} {coefficient:+.4g}" for name, coefficient in terms)

    @staticmethod
    def _find_judgement(fit):
        """The fit's error beside the bench scatter, and whether it beat it."""
        places = Analyze.ERROR_PLACES

        if fit.replicate_spread is None:
            return (f"off by {fit.leave_one_out_rmse:.{places}f}, with no setup run twice to "
                    f"judge it against")

        spread, degrees_of_freedom = fit.replicate_spread
        repeats = "repeat" if degrees_of_freedom == 1 else "repeats"
        judged = (f"off by {fit.leave_one_out_rmse:.{places}f} against a bench scatter of "
                  f"{spread:.{places}f} from {degrees_of_freedom} {repeats}")

        # Leaving the reader to compare the two numbers is how a fit that said nothing gets
        # quoted as a finding, so the line says it outright. Two numbers that print the same
        # have not been separated, so the call is made at the decimals shown.
        if round(fit.leave_one_out_rmse, places) > round(spread, places):
            return (f"{judged}, which is worse than the bench repeating itself, so this fit "
                    f"has earned no conclusion")

        return judged

    @staticmethod
    def _find_setting_words(names):
        """Settings as a reader names them, run together into one phrase."""
        return " and ".join(Analyze.SETTING_LABELS.get(name, name) for name in names)

    @staticmethod
    def _find_column_widths(rows):
        """Each column as wide as its own longest cell, so one long name shifts nothing."""
        return [max(len(cell) for cell in column) for column in zip(*rows)]

    @staticmethod
    def _find_number(value, places):
        """A value as the table prints it, or a dash where there is no number."""
        if value is None:
            return Analyze.MISSING

        return str(value) if places is None else f"{value:.{places}f}"

    @staticmethod
    def _find_sections_apart(sections):
        """The sections one after another, a blank line between any two that have lines."""
        lines = []

        for section in [section for section in sections if section]:
            if lines:
                lines.append("")

            lines.extend(section)

        return lines

    @staticmethod
    def _find_type(entry):
        """A plain word for the kind of record the entry is about."""
        return "reading" if entry.model.endswith("Reading") else entry.model.lower()

    @staticmethod
    def _find_entries_in_order(entries):
        """The entries as a reader wants them: by run, then by the minute of the reading."""
        def when(entry):
            parts = entry.id.split(":")

            # A check hands its worst offender back first, which puts minute 225 above 95.
            # A run left out whole has no minute, so -1 sets it before its own readings.
            minute = int(parts[-1]) if parts[-1].isdigit() else -1

            return parts[0], minute, entry.id

        return sorted(entries, key=when)
