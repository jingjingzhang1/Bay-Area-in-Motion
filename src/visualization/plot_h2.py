"""Render the final nine-county H2 figures from the prepared HY2a county panel."""

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, MultipleLocator, PercentFormatter, StrMethodFormatter
import pandas as pd

from src.utils.config import BAY_AREA_COUNTIES, PRE_COVID_YEAR, TABLES_DIR, YEARS
from src.utils.helpers import save_figure

POST_YEAR = YEARS[-1]
BEFORE = "#52677b"
AFTER = "#087b79"
INK = "#182d3b"
MUTED = "#465967"
GRID = "#dce4e8"


def load_comparison():
    """Read the county panel and pair the nine counties at the two endpoints."""
    source = TABLES_DIR / "hy2a_county_2017_2023.csv"
    panel = pd.read_csv(source, dtype={"county_fips": str})
    panel["acs_minus_lodes"] = panel["daytime_proxy_acs"] - panel["daytime_proxy_lodes"]
    endpoints = panel.loc[panel.year.isin([PRE_COVID_YEAR, POST_YEAR])]
    paired = endpoints.pivot(
        index="county_fips", columns="year",
        values="work_from_home_pct",
    ).sort_index()
    if set(paired.index) != set(BAY_AREA_COUNTIES) or paired.isna().any().any():
        raise ValueError("H2 requires one complete endpoint pair for each Bay Area county.")
    paired.index = paired.index.map(BAY_AREA_COUNTIES)
    return panel, paired


def setup_axis(ax, grid_axis):
    ax.set_axisbelow(True)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0, pad=7, colors=MUTED)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)


def heading(fig, title, subtitle):
    fig.text(0.045, 0.945, title, fontsize=23, weight="bold", color=INK, va="top")
    fig.text(0.045, 0.878, subtitle, fontsize=11, color=MUTED, va="top")


def footer(fig, text):
    fig.text(0.045, 0.025, text, fontsize=9, color=MUTED, va="bottom", linespacing=1.35)


def plot_county_estimates(panel):
    fig, axes = plt.subplots(3, 3, figsize=(12, 8.4), sharex=True)
    fig.subplots_adjust(left=0.095, right=0.97, top=0.77, bottom=0.13, wspace=0.34, hspace=0.42)
    heading(fig, "ACS and LODES daytime estimates by county",
            "Both estimates start with the same resident population. Each panel has its own scale.")
    for ax, (county, rows) in zip(axes.flat, panel.groupby("county_name")):
        data = rows.set_index("year").reindex(YEARS)
        setup_axis(ax, "y")
        ax.axvspan(2019.65, 2020.35, color="#edf1f3", zorder=0)
        ax.plot(YEARS, data["daytime_proxy_acs"] / 1000, label="ACS-based estimate",
                color=AFTER, marker="o", linewidth=1.9, markersize=4)
        ax.plot(YEARS, data["daytime_proxy_lodes"] / 1000, label="LODES-based estimate",
                color=BEFORE, marker="s", linestyle="--", linewidth=1.9, markersize=4)
        ax.set_title(county, loc="left", color=INK, weight="bold", fontsize=11)
        ax.set_xticks(YEARS)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=3, integer=True))
        ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.04, 0.85),
               frameon=False, ncol=2, labelcolor=INK)
    fig.supylabel("Estimated daytime population (thousands)", x=0.025, color=INK, fontsize=11)
    footer(fig, "Sources  ACS 1-year (B01003, B08301, B08604) and LEHD LODES v8 (WAC/RAC, primary jobs).\n"
                "Neither proxy is available in 2020. Napa’s ACS estimate is also missing in 2021–22.")
    return save_figure(fig, "fig_h2_daytime_estimates_by_county.png")


def plot_county_gap_trends(panel):
    gaps = panel.pivot(index="year", columns="county_name", values="acs_minus_lodes").reindex(YEARS)
    fig, (all_counties, detail) = plt.subplots(1, 2, figsize=(13.2, 6.6))
    fig.subplots_adjust(left=0.095, right=0.97, top=0.71, bottom=0.17, wspace=0.26)
    heading(fig, "ACS minus LODES by Bay Area county",
            "Above zero, ACS estimates a larger daytime population. Below zero, LODES estimates a larger one.")
    for ax, title in [(all_counties, "All nine counties"), (detail, "Eight counties without San Francisco")]:
        setup_axis(ax, "y")
        ax.axvspan(2019.65, 2020.35, color="#edf1f3", zorder=0)
        ax.axhline(0, color=MUTED, linewidth=1)
        ax.set(xticks=YEARS)
        ax.set_title(title, loc="left", color=INK, weight="bold", fontsize=11, pad=10)
        ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    colors = plt.get_cmap("tab10").colors
    markers = ["o", "s", "^", "v", "D", "P", "X", ">", "<"]
    for (county, values), color, marker in zip(gaps.items(), colors, markers):
        highlight = county == "San Francisco"
        axes = (all_counties,) if highlight else (all_counties, detail)
        for ax in axes:
            ax.plot(values.index, values / 1000, label=county, marker=marker,
                    color="#ae571d" if highlight else color,
                    linewidth=2.7 if highlight else 1.6, markersize=4.5,
                    zorder=4 if highlight else 3)
    all_counties.set_ylabel("Difference in estimates (thousands)")
    all_counties.yaxis.set_major_locator(MultipleLocator(40))
    detail.yaxis.set_major_locator(MultipleLocator(15))
    handles, labels = all_counties.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.039, 0.828),
               ncol=5, frameon=False, labelcolor=INK, fontsize=9)
    footer(fig, "Sources  ACS 1-year (B01003, B08301, B08604) and LEHD LODES v8 (WAC/RAC, primary jobs).\n"
                "No standard ACS 1-year release in 2020. Napa also lacks resident-worker estimates in 2021–22.")
    return save_figure(fig, "fig_h2_acs_minus_lodes_by_county.png")


def plot_remote_work(paired):
    remote = paired
    fig, ax = plt.subplots(figsize=(11.7, 6.3))
    fig.subplots_adjust(left=0.105, right=0.96, top=0.81, bottom=0.18)
    heading(fig, "Working from home increased in all nine counties",
            "Share of resident workers who reported working from home")
    setup_axis(ax, "y")
    rows = range(len(paired))
    for year, offset, color, period in [
        (PRE_COVID_YEAR, -0.17, BEFORE, "before COVID-19"),
        (POST_YEAR, 0.17, AFTER, "after pandemic onset"),
    ]:
        bars = ax.bar([row + offset for row in rows], remote[year], width=0.31,
                      color=color, label=f"{year} {period}")
        ax.bar_label(bars, fmt="%.1f%%", padding=4, fontsize=9, color=INK)
    labels = [county.replace(" ", "\n") for county in paired.index]
    ax.set(xticks=rows, xticklabels=labels, ylim=(0, 30),
           ylabel="Worked from home (% of resident workers)")
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
    ax.legend(loc="upper left", frameon=False, labelcolor=INK, fontsize=9, ncol=2)
    footer(fig, "Source  ACS 1-year B08301, worked from home (021E) divided by total resident workers (001E).")
    return save_figure(fig, "fig_h2_remote_work_before_after.png")


def main():
    panel, paired = load_comparison()
    for path in [plot_county_estimates(panel),
                 plot_remote_work(paired), plot_county_gap_trends(panel)]:
        print(path)


if __name__ == "__main__":
    main()
