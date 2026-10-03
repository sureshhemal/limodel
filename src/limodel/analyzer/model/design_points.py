"""The two settings each run was made at, in the units the fitting works in."""

import math


class DesignPoints:
    """Every setting of every run, logged then centred and scaled to -1..1, and the way back.

    Logs because current density and feed ratio each span a four- to sixfold range. Coded
    units because they keep the quadratic terms from swamping the linear ones. A setting held
    at one value across these runs is dropped rather than refused, and named as dropped.
    """

    SETTING_NAMES = ("current_density_ma_cm2", "feed_mg_li_ratio", "charge_per_li_offered")
    CODED_NAMES = ("x1", "x2", "x3")

    def __init__(self, results):
        self.results = list(results)

    def find_coded_rows(self):
        """One coded point per run; None when a setting is missing or none of them varies."""
        scales = self.find_scales()
        log_rows = self.find_log_rows()

        if scales is None or log_rows is None:
            return None

        return [self.find_coded_from_logs(row, scales) for row in log_rows]

    def find_coded_from_real(self, real_row):
        """A point in mA/cm2 and mol/mol, in coded units."""
        scales = self.find_scales()
        logs = self.find_logs_of(real_row)

        if scales is None or logs is None:
            return None

        return self.find_coded_from_logs(logs, scales)

    def find_real_from_coded(self, coded_row):
        """A coded point back in mA/cm2 and mol/mol, which is how the answer must be read."""
        scales = self.find_scales()

        if scales is None or coded_row is None or len(coded_row) != len(scales):
            return None

        if any(coded is None for coded in coded_row):
            return None

        # A dropped setting has no half-width, so it reads back as the one value it was held
        # at whatever coded value the search offers for it.
        return tuple(math.exp(centre + coded * half_width)
                     for coded, (centre, half_width) in zip(coded_row, scales))

    def find_kept_settings(self):
        """The settings that vary across these runs, the only ones a term can be built on."""
        scales = self.find_scales()

        if scales is None:
            return None

        return tuple(name for name, (_, half_width) in zip(self.SETTING_NAMES, scales)
                     if half_width != 0)

    def find_dropped_settings(self):
        """The settings held at one value, which the report should say the fit is blind to."""
        kept = self.find_kept_settings()

        if kept is None:
            return None

        return tuple(name for name in self.SETTING_NAMES if name not in kept)

    def find_usable_coded_names(self):
        """The settings that vary, under the names the polynomial knows them by."""
        kept = self.find_kept_settings()

        if kept is None:
            return None

        return tuple(coded for name, coded in zip(self.SETTING_NAMES, self.CODED_NAMES)
                     if name in kept)

    def find_coded_from_logs(self, logs, scales):
        """Where each logged setting sits between the lowest run and the highest."""
        # A dropped setting sits at 0, the one place it was ever run. Its terms are left out
        # by name, so a column of zeroes never reaches a fit.
        return tuple(0.0 if half_width == 0 else (value - centre) / half_width
                     for value, (centre, half_width) in zip(logs, scales))

    def find_scales(self):
        """The centre and half-width of each logged setting; None when not one of them varies."""
        log_rows = self.find_log_rows()

        if not log_rows:
            return None

        scales = []

        for column in zip(*log_rows):
            lowest, highest = min(column), max(column)
            scales.append(((highest + lowest) / 2, (highest - lowest) / 2))

        # Runs that moved nothing carry no information about anything, so there is no design.
        if all(half_width == 0 for _, half_width in scales):
            return None

        return tuple(scales)

    def find_log_rows(self):
        """Both settings of every run, logged; None when one of them is unusable."""
        rows = []

        for result in self.results:
            row = self.find_logs_of([getattr(result, name) for name in self.SETTING_NAMES])

            if row is None:
                return None

            rows.append(row)

        return rows

    def find_logs_of(self, settings):
        """None on a missing or non-positive setting, which has no logarithm."""
        if settings is None or len(settings) != len(self.SETTING_NAMES):
            return None

        if any(value is None or value <= 0 for value in settings):
            return None

        return tuple(math.log(value) for value in settings)
