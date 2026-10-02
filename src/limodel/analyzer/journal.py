"""The record of what the analysis left out, kept as the analysis goes along."""

from dataclasses import dataclass
from enum import Enum


class Action(Enum):
    """What was done to a record, spelled the way the report says it."""

    DROP = "dropped"   # the whole record is out of the modelling
    SKIP = "skipped"   # the record stays, one of its values does not

    def __str__(self) -> str:
        """The word itself, e.g. `dropped`, for printed lines."""
        return self.value


@dataclass(frozen=True)
class Entry:
    """One thing the analysis left out, and why.

    `id` and `model` locate it: every model carries an id, so "AJ" is a run, "AJ:conc:120"
    a tank reading and "AJ:120" a power reading. `field_name` is empty for a drop, because
    a drop is about the whole record rather than one of its values.

    The reason travels with the id so the terminal can say more than a count. Anything that
    disappears without a reason looks like a bug in the program.
    """

    action: Action
    id: str
    model: str
    reason: str
    field_name: str = ""


class Journal:
    """Holds what every stage of the analysis set aside, so one reader can see all of it.

    It is made empty and handed to the analyzer, which hands it on down. Each stage writes
    to the same one, in the order things happened, so nothing has to pass exclusions back up
    through its return value. Nothing here prints; the command reads it when the analysis is
    over and does the talking.
    """

    def __init__(self):
        self._entries: list[Entry] = []

    @property
    def entries(self) -> tuple[Entry, ...]:
        """Everything written down so far, in the order it was written."""
        return tuple(self._entries)

    def drop(self, record, reason: str):
        """Writes down one record that will not be modelled, and why."""
        self._write(Action.DROP, record, reason)

    def skip(self, record, field_name: str, reason: str):
        """Writes down one value that will not be used, and why. The record itself stays."""
        self._write(Action.SKIP, record, reason, field_name)

    def _write(self, action, record, reason, field_name=""):
        """One entry, taking the id and the model name from the record itself.

        Reading them here rather than at the call site means the two can never disagree.
        """
        self._entries.append(Entry(action, record.id, type(record).__name__, reason, field_name))
