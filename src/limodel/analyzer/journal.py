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

    `id` locates it, because every model carries one: "AJ" is a run, "AJ:conc:120" a tank
    reading. `field_name` is empty for a drop, which is about the whole record.
    """

    action: Action
    id: str
    model: str
    reason: str
    field_name: str = ""


class Journal:
    """What every stage of the analysis set aside, in one place.

    Made empty and handed to the analyzer, which hands it on. Nothing here prints; the
    command reads it when the analysis is over.
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
        # A row refused at the door never becomes the record it would have been, so it says
        # what kind it is itself. Everything else is named by its class.
        model = getattr(record, "model", None) or type(record).__name__

        self._entries.append(Entry(action, record.id, model, reason, field_name))
