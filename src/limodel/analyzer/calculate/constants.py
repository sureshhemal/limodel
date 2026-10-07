"""Every constant the calculations lean on, in one place."""

FARADAY_C_PER_MOL = 96485.0
LI_G_PER_MOL = 6.94
MG_G_PER_MOL = 24.305

# A litre of these dilute salt solutions weighs a kilogram closely enough to read grammes
# on the balance as litres in the tank.
SOLUTION_G_PER_L = 1000.0

CONCENTRATE = "conc"
DILUTE = "dil"
RINSE = "rinse"

# Each tank was weighed empty before the run, and the empty weight lives in its own column.
TARE_FIELD_BY_TANK = {
    CONCENTRATE: "tare_conc_g",
    DILUTE: "tare_dil_g",
    RINSE: "tare_rinse_g",
}
