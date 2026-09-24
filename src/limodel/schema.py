"""Column definitions (names, types, units, required) for setups, readings and samples."""

# Issue codes a row may carry. They record what is wrong with a row, never what to do
# about it: checks.py decides that, so the policy can change without editing data.
# Problems the code can work out for itself (mislabelled sample IDs, duplicates,
# out-of-range values, missing lab results) are not stored here.
UNLABELLED_VALUES = "UNLABELLED_VALUES"
"""Lab values recorded in a row that carries no sample ID, so they belong to no sample."""

ISSUE_CODES = frozenset({UNLABELLED_VALUES})
