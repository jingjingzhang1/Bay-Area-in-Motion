"""Rebuild the Vital Signs population-change map from the processed shapefile.

Run from the project root: python -m src.visualization.plot_population_change
Percent change is calculated from pop_2019 and pop_2023.
"""
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from src.utils.config import FIGURES_DIR, PROJECT_CRS, VITAL_SIGNS_SHAPEFILE_DIR, WATER_LAYER
from src.visualization.maps import add_water


INPUT = VITAL_SIGNS_SHAPEFILE_DIR / "vital_signs_population_tracts.shp"
OUTPUT = FIGURES_DIR / "fig_population_change_2019_2023.png"
TITLE = "Bay Area Population Change from 2019 to 2023"
CLASSIFICATION = "User-defined fixed breaks (7 classes)"
BREAKS = [-np.inf, -20, -10, -2, 2, 10, 20, np.inf]
LABELS = ["<= -20%", "(-20%, -10%]", "(-10%, -2%]", "(-2%, 2%]",
          "(2%, 10%]", "(10%, 20%]", "> 20%"]
COLORS = ["#8c2d04", "#d94801", "#fd8d3c", "#fff2b2", "#9ecae1", "#4292c6", "#08519c"]
NO_DATA = "#bdbdbd"


def population_change(tracts):
    """Conventional percent change; invalid counts or zero baselines are missing."""
    baseline = pd.to_numeric(tracts["pop_2019"], errors="coerce")
    current = pd.to_numeric(tracts["pop_2023"], errors="coerce")
    valid = (baseline > 0) & (current >= 0) & np.isfinite(baseline) & np.isfinite(current)
    return (current.where(valid) - baseline.where(valid)) / baseline.where(valid) * 100


def classify(values):
    """Right-closed fixed intervals; missing/sentinel/nonfinite values stay missing."""
    values = pd.to_numeric(values, errors="coerce")
    values = values.mask((values == -99999) | ~np.isfinite(values))
    return pd.cut(values, bins=BREAKS, labels=LABELS, right=True)


def add_scale_bar(ax, bounds):
    """A 40 km bar in the map's UTM meter coordinates."""
    xmin, ymin, xmax, ymax = bounds
    x = xmin + (xmax - xmin) * 0.07
    y = ymin + (ymax - ymin) * 0.055
    height = (ymax - ymin) * 0.007
    for i, color in enumerate(["#263238", "white"]):
        ax.add_patch(Rectangle((x + i * 20000, y), 20000, height,
                               facecolor=color, edgecolor="#263238", lw=0.8, zorder=6))
    for distance, label in [(0, "0"), (20000, "20"), (40000, "40 km")]:
        ax.text(x + distance, y - height, label, ha="center", va="top", fontsize=9, zorder=6)


def plot_population_change(input_path=INPUT, output_path=OUTPUT):
    """Draw all supplied tracts, with a north arrow, scale, legend and source."""
    tracts = gpd.read_file(input_path)
    if tracts.crs is None:
        raise ValueError("The input shapefile must declare a coordinate reference system.")
    if not {"pop_2019", "pop_2023"}.issubset(tracts.columns):
        raise ValueError("The input shapefile must contain pop_2019 and pop_2023.")
    if tracts.empty or tracts.geometry.is_empty.any() or tracts.geometry.isna().any():
        raise ValueError("The input must contain nonempty tract geometries.")
    tracts = tracts.to_crs(PROJECT_CRS)
    classes = classify(population_change(tracts))
    colors = classes.astype(object).map(dict(zip(LABELS, COLORS))).fillna(NO_DATA)

    fig, ax = plt.subplots(figsize=(12, 11), facecolor="white")
    fig.subplots_adjust(left=0.02, right=0.76, bottom=0.13, top=0.89)
    ax.set_facecolor("#e6f1f5")
    tracts.plot(ax=ax, color=colors, edgecolor="#ffffff", linewidth=0.12, zorder=2)
    if WATER_LAYER.exists():
        add_water(ax, PROJECT_CRS)
    # Derive outlines from the same committed geometry; no external boundary download.
    counties = tracts[["county", "geometry"]].dissolve(by="county")
    counties.boundary.plot(ax=ax, color="#59656b", linewidth=0.45, zorder=4)
    counties.dissolve().boundary.plot(ax=ax, color="#263238", linewidth=0.9, zorder=5)

    xmin, ymin, xmax, ymax = tracts.total_bounds
    width, height = xmax - xmin, ymax - ymin
    bounds = (xmin - width * 0.07, ymin - height * 0.08,
              xmax + width * 0.07, ymax + height * 0.06)
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[1], bounds[3])
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    for spine in ax.spines.values():
        spine.set_visible(False)
    add_scale_bar(ax, bounds)
    # Grid north in NAD83 / UTM 10N; explicitly labelled to avoid implying true north.
    ax.annotate("N", xy=(0.91, 0.94), xytext=(0.91, 0.84), xycoords="axes fraction",
                ha="center", va="center", fontsize=16, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="#263238", lw=1.8), zorder=6)
    ax.text(0.91, 0.80, "Grid north", transform=ax.transAxes, ha="center", fontsize=8)

    handles = [Patch(facecolor=color, edgecolor="#777777", linewidth=0.4, label=label)
               for color, label in zip(COLORS, LABELS)]
    handles.append(Patch(facecolor=NO_DATA, label=f"No data ({classes.isna().sum()} tracts)"))
    handles.append(Line2D([0], [0], color="#263238", lw=0.9, label="Mapped Bay Area boundary"))
    handles.append(Line2D([0], [0], color="#59656b", lw=0.45, label="County boundaries"))
    fig.legend(handles=handles, title="Population change (%)\nNegative: decline\nPositive: growth",
               loc="center left", bbox_to_anchor=(0.76, 0.54), frameon=False,
               labelspacing=1.0, fontsize=11, title_fontsize=11)
    fig.text(0.78, 0.29, "Classification:\nUser-defined fixed breaks\n7 classes; right-closed intervals",
             fontsize=9, color="#455a64", linespacing=1.5)
    fig.suptitle(TITLE, fontsize=20, fontweight="bold", y=0.96)
    fig.text(0.5, 0.915, "MTC Vital Signs | Bay Area census tracts", ha="center", fontsize=12, color="#455a64")
    fig.text(0.06, 0.075, "Source: processed Vital Signs population tracts, pop_2019 and pop_2023. Projection: NAD83 / UTM zone 10N (EPSG:26910).",
             fontsize=9)
    fig.text(0.06, 0.05, "Percent change = (2023 population - 2019 population) / 2019 population x 100. Zero baselines or invalid counts are gray.", fontsize=9)
    fig.text(0.06, 0.03, "Boundaries derived from Vital Signs tracts. Estimates are based on ACS 5-year releases; periods overlap.", fontsize=9)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=240, facecolor=fig.get_facecolor())
    plt.close(fig)
    counts = classes.value_counts(sort=False).reindex(LABELS, fill_value=0)
    print(f"{CLASSIFICATION}: {counts.to_dict()}; no data: {classes.isna().sum()}")
    return output_path


if __name__ == "__main__":
    print(plot_population_change())
