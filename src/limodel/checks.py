"""Finds everything wrong with the data, and reports it instead of raising."""

from dataclasses import dataclass

import pandera.errors

from limodel.schema import Run, Sample, StackReading, TankReading

SCHEMAS = {
    "runs": Run,
    "stack_readings": StackReading,
    "tank_readings": TankReading,
    "samples": Sample,
}

# Columns that say which row a problem is in, in the order they read best.
WHERE = ["run_code", "minute", "tank", "sample_id"]


@dataclass(frozen=True)
class Problem:
    """One thing wrong with one row, described so it can be fixed in the workbook."""
    table: str
    where: str
    column: str
    value: str
    problem: str

    def __str__(self):
        return f"{self.table:15s} {self.where:22s} {self.column:20s} {self.value:14s} {self.problem}"


def find_problems(tables):
    """Every problem in the given tables, worst first. Never raises."""
    problems = []

    for name, schema in SCHEMAS.items():
        table = tables.get(name)

        if table is None:
            problems.append(Problem(name, "", "", "", "file is missing"))
            continue

        problems.extend(_schema_problems(name, schema, table))

    return problems


def _schema_problems(name, schema, table):
    """What the schema rejects: wrong types, missing required values, broken rules."""
    try:
        schema.validate(table, lazy=True)
        return []
    except pandera.errors.SchemaErrors as errors:
        cases = errors.failure_cases[errors.failure_cases.apply(_is_worth_reporting, axis=1)]
        problems = [_as_problem(name, table, case) for _, case in cases.iterrows()]
        return list(dict.fromkeys(problems))


def _is_worth_reporting(case):
    """One bad value is reported by several rules; keep the one that explains it."""
    check, value = str(case.get("check")), str(case.get("failure_case"))

    if check.startswith("dtype("):
        return False  # the coercion failure already says the value is not a number

    return not value.startswith(("TypeError(", "ValueError("))


def _as_problem(name, table, case):
    return Problem(
        table=name,
        where=_where(table, case.get("index")),
        column=str(case.get("column") or ""),
        value=str(case.get("failure_case")),
        problem=_explain(str(case.get("check"))),
    )


def _where(table, index):
    """'AK minute 0 conc' — whichever of the identifying columns the table has."""
    if index is None or index not in table.index:
        return ""

    row = table.loc[index]
    parts = []
    for column in WHERE:
        if column in table.columns and str(row[column]) != "nan":
            parts.append(f"minute {row[column]}" if column == "minute" else str(row[column]))

    return " ".join(parts)


def _explain(check):
    """Plain wording for the rule that failed."""
    if check.startswith("coerce_dtype"):
        return "not a number"
    if check == "field_uniqueness":
        return "used more than once"
    if check == "not_nullable":
        return "required, but blank"
    if check == "column_in_schema":
        return "unexpected column"
    if check == "column_in_dataframe":
        return "column is missing"
    if check.startswith("isin"):
        return f"not one of {check[5:-1]}"
    if check.startswith(("greater_than", "less_than")):
        return f"outside its range ({check})"

    return check
