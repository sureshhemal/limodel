"""The shape every check shares."""

from abc import ABC, abstractmethod


class Check(ABC):
    """One rule about one kind of value: readings in, the worst offender out.

    A check only decides. It never writes to the journal and never clears a value; the
    inspector that runs it does both. That way a check can be tried on a handful of
    readings and simply asked what it thinks.

    `find` answers with the reading at fault, which of its values to clear, and why. The
    value to clear is named by the check because a check that holds two instruments against
    each other has to say which of the two it blames.
    """

    field_name: str   # the value it judges, e.g. "weight_g"
    label: str        # how that value is called in a sentence, e.g. "weight"

    def judgeable(self, readings):
        """The readings this check can say anything about."""
        return [reading for reading in readings if getattr(reading, self.field_name) is not None]

    @abstractmethod
    def find(self, readings):
        """The reading at fault, the value to clear and the reason. Or None."""
