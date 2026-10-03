"""A table split into the rows a schema takes and the rows it refuses."""

import pandas as pd
import pandera.errors

from limodel.sources.rejected_row import RejectedRow

BLANK = "not_nullable"
NOT_A_NUMBER = "coerce_dtype"
USED_TWICE = "uniqueness"
NOT_ALLOWED = "isin"


class RowsTheSchemaAccepts:
    """Keeps the rows a schema takes and writes down the rest, rather than refusing the file.

    Refusing the whole file was the old rule, and one blank cell in one run stopped every
    other run loading. A row that cannot be read is a finding like any other: it is left out,
    the reason is kept, and the rest of the work goes on.
    """

    def __init__(self, schema, model: str, key_column: str):
        self.schema = schema
        self.model = model              # what the row would have become, for the journal
        self.key_column = key_column    # the column that names a row, so a reader can find it

    def find_kept_and_refused(self, table):
        """The rows that pass, and a RejectedRow for each one that does not."""
        try:
            return self.schema.validate(table, lazy=True), ()
        except pandera.errors.SchemaErrors as refused:
            return self._find_second_try(table, refused)

    def _find_second_try(self, table, refused):
        """The table again without the rows that failed; the file itself if none can be."""
        failures = self._find_failures_by_row(refused)

        # A fault with no row behind it is the file's shape, not one row's contents, and
        # dropping rows cannot mend it.
        if not failures:
            raise refused

        kept = table.drop(index=list(failures))

        return self.schema.validate(kept, lazy=True), self._find_rejections(table, failures)

    def _find_rejections(self, table, failures):
        """One entry per refused row, in the order the rows sit in the file."""
        return tuple(RejectedRow(id=self._find_name(table, at), model=self.model,
                                 reason="; ".join(reasons))
                     for at, reasons in sorted(failures.items()))

    def _find_name(self, table, at):
        """What to call the row: its key if it has one, else where it sits in the file."""
        if self.key_column in table.columns and not pd.isna(table.at[at, self.key_column]):
            return str(table.at[at, self.key_column])

        return f"line {at + 2}"      # the header is line 1 and the index starts at 0

    def _find_failures_by_row(self, refused):
        """Every fault that belongs to a row, gathered under that row."""
        cases = refused.failure_cases
        found = {}

        if "index" not in cases.columns:
            return found

        for row in cases.to_dict("records"):
            at = row.get("index")

            if at is None or pd.isna(at):
                continue

            found.setdefault(int(at), []).append(self._find_reason(row))

        return found

    @staticmethod
    def _find_reason(case):
        """Why the row was refused, in words rather than in the schema's own language."""
        column = case.get("column") or "a value"
        check = str(case.get("check") or "")
        value = case.get("failure_case")

        if BLANK in check:
            return f"{column} is blank"

        if NOT_A_NUMBER in check:
            return f"{column} is {value!r}, which is not a number"

        # Both rows go when an id is used twice: neither can be shown to be the right one.
        if USED_TWICE in check:
            return f"{column} {value!r} is used more than once"

        if NOT_ALLOWED in check:
            return f"{column} is {value!r}, which is not one of the ones allowed"

        return f"{column} is {value!r}, outside what the file allows ({check})"
