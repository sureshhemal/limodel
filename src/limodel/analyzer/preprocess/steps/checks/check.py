"""The shape every check shares."""

from abc import ABC, abstractmethod


class Check(ABC):
    """One rule about one kind of value: readings in, the worst offender out.

    A check only decides. The inspector writes it down and clears it. `find` says which
    value to clear, because a paired check has to blame one instrument of two.
    """

    field_name: str   # the value it judges, e.g. "weight_g"
    label: str        # how that value is called in a sentence, e.g. "weight"

    def find_judgeable_readings(self, readings):
        """The readings this check can say anything about."""
        return [reading for reading in readings if getattr(reading, self.field_name) is not None]

    @abstractmethod
    def find_worst_offender(self, readings):
        """The reading at fault, the value to clear and the reason. Or None."""
