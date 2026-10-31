"""County ACS charts: work-from-home share and LODES vs ACS daytime proxies."""
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from src.utils.helpers import set_chart_style, add_caption, save_figure

set_chart_style()


def plot_wfh_share(county, highlight="San Francisco", name="fig_acs_wfh_share_by_county.png"):
    """Work-from-home share by county over time, with one county highlighted."""
    fig, ax = plt.subplots(figsize=(10, 6))
    for county_name, rows in county.dropna(subset=["work_from_home_pct"]).groupby("county_name"):
        main = county_name == highlight
        ax.plot(rows["year"], rows["work_from_home_pct"], marker="o",
                lw=3 if main else 1.5, alpha=1 if main else 0.75,
                color="#c74936" if main else None, label=county_name, zorder=4 if main else 2)
    years = sorted(county["year"].unique())
    ax.set_title(f"Work-from-home share by Bay Area county, {years[0]}-{years[-1]}")
    ax.set_xlabel("Year")
    ax.set_ylabel("Workers who worked from home (% of resident workers)")
    ax.set_xticks(years)
    ax.axvspan(2019.75, 2020.25, color="#e5e7eb", alpha=0.65, zorder=0)
    ax.grid(alpha=0.2)
    ax.legend(loc="upper left", ncol=3, fontsize=8, frameon=False)
    add_caption(fig, "Source: ACS 1-year B08301. No standard 2020 ACS 1-year release (shaded); "
                     "Napa 2021-2022 not published. No values are interpolated.")
    return save_figure(fig, name)


def plot_lodes_vs_acs(county, year, name="fig_acs_lodes_vs_acs_daytime.png"):
    """Scatter of the LODES and ACS county daytime proxies in one year, with a 1:1 line."""
    rows = county[county["year"] == year].dropna(subset=["daytime_proxy_lodes", "daytime_proxy_acs"])
    lo = min(rows["daytime_proxy_lodes"].min(), rows["daytime_proxy_acs"].min()) * 0.85
    hi = max(rows["daytime_proxy_lodes"].max(), rows["daytime_proxy_acs"].max()) * 1.08
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.plot([lo, hi], [lo, hi], ls="--", color="#8aacc4", label="Equal values")
    ax.scatter(rows["daytime_proxy_acs"], rows["daytime_proxy_lodes"], s=70, color="#2879aa", zorder=3)
    for _, r in rows.iterrows():
        ax.annotate(r["county_name"], (r["daytime_proxy_acs"], r["daytime_proxy_lodes"]),
                    xytext=(6, 6), textcoords="offset points", fontsize=9)
    millions = FuncFormatter(lambda x, _: f"{x / 1e6:.1f}M")
    ax.xaxis.set_major_formatter(millions)
    ax.yaxis.set_major_formatter(millions)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_title(f"LODES vs ACS daytime population proxies by county, {year}")
    ax.set_xlabel("ACS proxy: population + workplace workers - resident workers (people)")
    ax.set_ylabel("LODES proxy: population + WAC - RAC (people)")
    ax.grid(alpha=0.18)
    ax.legend(frameon=False)
    add_caption(fig, f"Source: ACS 1-year B01003, B08301, B08604 and LEHD LODES8 WAC/RAC, {year}. "
                     "Both are commuting-based proxies, not counts of people present.")
    return save_figure(fig, name)
