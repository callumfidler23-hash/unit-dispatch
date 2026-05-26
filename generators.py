"""
Generator fleet. Loosely based on IESO connected generator registry.
Fill in real capacity/cost figures from the IESO generator list as you go.
Coords are approximate zone centroids for now — replace with actuals.
"""

import pandas as pd

# fuel type -> approximate marginal cost ($/MWh), rough Ontario figures
FUEL_COST = {
    "nuclear": 8,
    "hydro":   12,
    "wind":    0,
    "solar":   0,
    "gas":     85,
    "gas_cc":  70,
    "biofuel": 110,
}

# columns: name, fuel, zone, p_min (MW), p_max (MW), ramp (MW/hr), must_run, lat, lon
GENERATORS = [
    # nuclear -- must-run, very flat ramp
    ("Darlington",   "nuclear", "Toronto",  440, 3512,  50, True,  43.87, -78.71),
    ("Pickering",    "nuclear", "Toronto",  440, 3100,  50, True,  43.81, -79.07),
    ("Bruce",        "nuclear", "West",    1000, 6400,  80, True,  44.32, -81.60),

    # hydro
    ("Niagara",      "hydro",   "Niagara",   0, 1800, 600, False, 43.08, -79.07),
    ("Ottawa River", "hydro",   "East",      0,  950, 400, False, 45.35, -76.35),
    ("NW Hydro",     "hydro",   "Northwest", 0,  600, 300, False, 49.00, -88.00),

    # wind (no fuel cost, curtailable)
    ("Bruce Wind",   "wind",    "West",      0,  900, 900, False, 44.50, -81.40),
    ("Amaranth",     "wind",    "West",      0,  200, 200, False, 44.00, -80.20),
    ("East Wind",    "wind",    "East",      0,  300, 300, False, 44.50, -76.50),

    # gas peakers
    ("Portlands",    "gas",     "Toronto",   0,  550, 275, False, 43.64, -79.34),
    ("Lennox",       "gas",     "East",      0, 2100, 525, False, 44.27, -76.82),
    ("Greenfield",   "gas_cc",  "Southwest", 0,  280, 280, False, 42.95, -82.40),
    ("Goreway",      "gas_cc",  "Toronto",   0,  875, 437, False, 43.77, -79.63),
]


def get_fleet():
    cols = ["name", "fuel", "zone", "p_min", "p_max", "ramp_mw_hr", "must_run", "lat", "lon"]
    df = pd.DataFrame(GENERATORS, columns=cols)
    df["cost"] = df["fuel"].map(FUEL_COST)
    return df


if __name__ == "__main__":
    print(get_fleet().to_string())
