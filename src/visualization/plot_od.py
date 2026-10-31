"""Charts from the LODES OD and WAC/RAC data."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.utils.helpers import tract_number, set_chart_style, add_caption, save_figure

set_chart_style()


def plot_top_corridors(corr_wide, n=8, name="fig_od_top_corridors_by_year.png"):
    """Line chart of the n largest county-to-county corridors over time."""
    years = list(corr_wide.columns)
    fig, ax = plt.subplots(figsize=(8, 5))
    for corridor, row in corr_wide.head(n).iterrows():
        ax.plot(years, row.values / 1000, marker="o", lw=1.8, label=corridor)
    ax.set_title(f"Top county-to-county commuting corridors, Bay Area, {years[0]}-{years[-1]}")
    ax.set_xlabel("Year")
    ax.set_ylabel("Commuters (thousands of jobs)")
    ax.set_xticks(years)
    ax.legend(fontsize=8, frameon=False, loc="center left", bbox_to_anchor=(1.01, 0.5))
    add_caption(fig, "Primary jobs where home and work are in different Bay Area counties. "
                     "Source: LEHD LODES8 OD (main).")
    return save_figure(fig, name)


def plot_tract_gain_loss(chg, start, end, n=10, name="fig_lodes_tract_gain_loss.png"):
    """Horizontal bars for the n tracts with the largest gain and the n with the largest loss in net jobs."""
    d = pd.concat([chg.nlargest(n, "delta_net_jobs"), chg.nsmallest(n, "delta_net_jobs")])
    d = d.assign(label="Tract " + d["tract_geoid"].apply(tract_number) + ", " + d["county_name"])
    d = d.sort_values("delta_net_jobs")
    colors = np.where(d["delta_net_jobs"] >= 0, "#1f77b4", "#e08214")
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh(d["label"], d["delta_net_jobs"] / 1000, color=colors)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_title(f"Census tracts with the largest gain and loss in net daytime jobs, Bay Area, {start}-{end}")
    ax.set_xlabel(f"Change in net jobs, {start} to {end} (thousands; jobs at work minus jobs at home)")
    ax.set_ylabel("Census tract")
    add_caption(fig, f"Top {n} gains (blue) and losses (orange). Net jobs = WAC minus RAC. "
                     f"Source: LEHD LODES8 WAC and RAC, {start} and {end}.")
    return save_figure(fig, name)
