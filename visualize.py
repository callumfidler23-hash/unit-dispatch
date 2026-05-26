"""
Plots dispatch results. Two outputs:
  1. dispatch stack (area chart by fuel type, 24 hours)
  2. zone map (choropleth of total generation by zone)
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import geopandas as gpd
from pathlib import Path

OUTPUTS = Path("outputs")

FUEL_COLORS = {
    "nuclear": "#7c3aed",
    "hydro":   "#2563eb",
    "wind":    "#16a34a",
    "solar":   "#eab308",
    "gas":     "#dc2626",
    "gas_cc":  "#f97316",
    "biofuel": "#78716c",
}


def plot_dispatch_stack(results_df):
    pivot = (
        results_df
        .groupby(["hour", "fuel"])["output_mw"]
        .sum()
        .unstack(fill_value=0)
    )

    # order fuels by cost (stack cheapest at bottom)
    fuel_order = ["nuclear", "hydro", "wind", "solar", "gas_cc", "gas", "biofuel"]
    cols = [c for c in fuel_order if c in pivot.columns]
    pivot = pivot[cols]

    fig, ax = plt.subplots(figsize=(12, 5))
    pivot.plot.area(ax=ax, color=[FUEL_COLORS.get(c, "grey") for c in pivot.columns], alpha=0.85)

    ax.set_xlabel("Hour")
    ax.set_ylabel("Generation (MW)")
    ax.set_title("Ontario Economic Dispatch — Hourly Stack")
    ax.legend(loc="upper left", fontsize=8)

    plt.tight_layout()
    fig.savefig(OUTPUTS / "dispatch_stack.png", dpi=150)
    plt.close()
    print("saved dispatch_stack.png")


def plot_zone_map(results_df, shapefile_path=None):
    """
    If you have an Ontario zone shapefile, pass the path.
    Otherwise falls back to a simple bar chart by zone.
    """
    zone_totals = (
        results_df
        .groupby("zone")["output_mw"]
        .sum()
        .reset_index()
        .rename(columns={"output_mw": "total_mw"})
    )

    if shapefile_path and Path(shapefile_path).exists():
        gdf = gpd.read_file(shapefile_path)
        # TODO: align zone name column in gdf to match zone_totals["zone"]
        gdf = gdf.merge(zone_totals, left_on="ZONE_NAME", right_on="zone", how="left")

        fig, ax = plt.subplots(figsize=(10, 8))
        gdf.plot(column="total_mw", ax=ax, legend=True, cmap="YlOrRd", missing_kwds={"color": "lightgray"})
        ax.set_title("Total Generation by Zone (MWh)")
        ax.axis("off")
        fig.savefig(OUTPUTS / "zone_map.png", dpi=150)
        plt.close()
        print("saved zone_map.png")

    else:
        # fallback: bar chart
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(zone_totals["zone"], zone_totals["total_mw"], color="#3b82f6")
        ax.set_ylabel("Total Output (MWh)")
        ax.set_title("Total Generation by Zone")
        plt.tight_layout()
        fig.savefig(OUTPUTS / "zone_bar.png", dpi=150)
        plt.close()
        print("saved zone_bar.png (no shapefile found, used bar chart fallback)")


def plot_generator_scatter(results_df, fleet_df):
    """
    Scatter of generators on lat/lon, sized by avg output, colored by fuel.
    """
    avg = results_df.groupby("generator")["output_mw"].mean().reset_index()
    merged = avg.merge(fleet_df[["name", "lat", "lon", "fuel"]], left_on="generator", right_on="name")

    fig, ax = plt.subplots(figsize=(9, 7))
    for fuel, group in merged.groupby("fuel"):
        ax.scatter(
            group["lon"], group["lat"],
            s=group["output_mw"] / 5,
            c=FUEL_COLORS.get(fuel, "grey"),
            label=fuel, alpha=0.8, edgecolors="white", linewidths=0.5
        )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Generator Dispatch — Average Output (bubble size = MW)")
    ax.legend(fontsize=8)
    plt.tight_layout()
    fig.savefig(OUTPUTS / "generator_map.png", dpi=150)
    plt.close()
    print("saved generator_map.png")


if __name__ == "__main__":
    from generators import get_fleet

    results = pd.read_csv("data/processed/dispatch_results.csv")
    fleet = get_fleet()

    plot_dispatch_stack(results)
    plot_zone_map(results)
    plot_generator_scatter(results, fleet)
