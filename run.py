"""
Run the full pipeline for a given date.
Usage: python run.py --date 2024-01-15
"""

import argparse
import pandas as pd
import numpy as np

from generators import get_fleet
from dispatch import build_model, solve, extract_results
from visualize import plot_dispatch_stack, plot_zone_map, plot_generator_scatter


def load_demand_for_date(date_str):
    """
    Load real hourly demand from processed IESO data.
    Falls back to a synthetic profile if data isn't downloaded yet.
    """
    try:
        df = pd.read_csv("data/raw/demand_2024.csv")  # adjust col names after inspecting real file
        # TODO: filter to date_str, extract 24 hourly values
        raise NotImplementedError("parse real IESO demand file here")
    except (FileNotFoundError, NotImplementedError):
        print("using synthetic demand -- run fetch_data.py to get real IESO data")
        np.random.seed(hash(date_str) % 2**32)
        base = 14000 + 2000 * np.sin(np.linspace(0, np.pi, 24))
        return base + np.random.normal(0, 300, 24)


def main(date_str):
    print(f"\n--- dispatch for {date_str} ---")

    fleet = get_fleet()
    demand = load_demand_for_date(date_str)

    print(f"peak demand: {demand.max():.0f} MW  |  generators: {len(fleet)}")

    prob, p_vars, s_vars = build_model(fleet, demand)
    status = solve(prob)

    if status != "Optimal":
        print("model did not solve optimally -- check constraints")
        return

    results = extract_results(p_vars, fleet)
    results.to_csv("data/processed/dispatch_results.csv", index=False)

    plot_dispatch_stack(results)
    plot_zone_map(results)
    plot_generator_scatter(results, fleet)

    print("\ndone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="2024-01-15", help="YYYY-MM-DD")
    args = parser.parse_args()
    main(args.date)
