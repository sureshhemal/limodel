"""What each data file must look like."""

from limodel.schema.run import Run
from limodel.schema.sample import Sample
from limodel.schema.stack_reading import StackReading
from limodel.schema.tank_reading import TANKS, TankReading

__all__ = ["Run", "StackReading", "TankReading", "Sample", "TANKS"]
