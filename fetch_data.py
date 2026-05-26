"""
Pulls hourly demand and zonal price data from IESO open data.
Run this first before anything else.
"""

import requests
import pandas as pd
from pathlib import Path

RAW = Path("data/raw")

IESO_DEMAND_URL = "https://www.ieso.ca/-/media/Files/IESO/Power-Data/data-directory/HourlyDemands_YYYY.csv"
IESO_PRICE_URL  = "https://www.ieso.ca/-/media/Files/IESO/Power-Data/data-directory/PUB_HourlyHOEPPredispatch_YYYY.csv"

YEARS = [2023, 2024]


def fetch_demand(year):
    url = IESO_DEMAND_URL.replace("YYYY", str(year))
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    out = RAW / f"demand_{year}.csv"
    out.write_bytes(r.content)
    print(f"saved {out}")


def fetch_prices(year):
    url = IESO_PRICE_URL.replace("YYYY", str(year))
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    out = RAW / f"prices_{year}.csv"
    out.write_bytes(r.content)
    print(f"saved {out}")


def load_demand():
    frames = []
    for f in sorted(RAW.glob("demand_*.csv")):
        df = pd.read_csv(f)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def load_prices():
    frames = []
    for f in sorted(RAW.glob("prices_*.csv")):
        df = pd.read_csv(f)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    for yr in YEARS:
        fetch_demand(yr)
        fetch_prices(yr)
