"""The two metals the separation is about, each carrying what the sums need to know."""

from dataclasses import dataclass

from limodel.analyzer.calculate.constants import LI_G_PER_MOL, MG_G_PER_MOL


@dataclass(frozen=True)
class Metal:
    """A metal, its column in a lab sample, its molar mass and the charge an ion carries.

    The charge travels with the metal because a transport number is a share of the charge,
    not of the ions: magnesium moves two charges for every one lithium moves.
    """

    name: str
    field_name: str
    g_per_mol: float
    charge: int


LITHIUM = Metal(name="lithium", field_name="li_mg_l", g_per_mol=LI_G_PER_MOL, charge=1)
MAGNESIUM = Metal(name="magnesium", field_name="mg_mg_l", g_per_mol=MG_G_PER_MOL, charge=2)
