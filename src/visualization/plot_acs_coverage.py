"""Coverage figures and HTML extracted from the jurisdiction notebook."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from src.data.census_api import METRICS
from src.data.clean_acs_places import YEARS


def plot_places(roster, coverage, summary, output_dir):
    OUTPUT_DIR = Path(output_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    estimate_status_columns = [f"{metric}_status" for metric in METRICS]
    # HTML preserves the coverage status colors.
    from html import escape


    coverage_palette = {
        "Available": ("#d9efdf", "#14532d"),
        "Missing estimate": ("#fee2e2", "#991b1b"),
        "Place not published": ("#ffedd5", "#9a3412"),
        "2020 not released": ("#e5e7eb", "#374151"),
    }
    coverage_headers = {
        "county_name": "County", "jurisdiction_name": "Jurisdiction", "year": "Year",
        "population_status": "Population (B01003_001E)",
        "workers_residence_status": "Resident workers (B08301_001E)",
        "work_from_home_status": "Work from home (B08301_021E)",
        "workers_workplace_status": "Workplace workers (B08604_001E)",
    }
    view_columns = ["county_name", "jurisdiction_name", "year"] + estimate_status_columns

    def coverage_table_html(rows):
        header = "".join(f"<th>{escape(coverage_headers[column])}</th>" for column in view_columns)
        body = []
        for values in rows[view_columns].itertuples(index=False, name=None):
            cells = []
            for column, value in zip(view_columns, values):
                background, foreground = coverage_palette.get(str(value), ("#ffffff", "#111827"))
                cells.append(
                    f'<td style="background:{background};color:{foreground};'
                    f'padding:8px 10px;border-bottom:1px solid #ddd;text-align:left">'
                    f'{escape(str(value))}</td>'
                )
            body.append("<tr>" + "".join(cells) + "</tr>")
        return (
            '<div style="max-height:650px;overflow:auto;border:1px solid #ddd">'
            '<table style="border-collapse:collapse;font:13px Arial,sans-serif;width:100%">'
            '<thead style="position:sticky;top:0;background:#f3f4f6;text-align:left">'
            f'<tr>{header}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
        )

    partial_coverage = coverage.loc[
        coverage["availability"].eq("One or more estimates missing")
    ].sort_values(["county_name", "jurisdiction_name", "year"])
    legend = " ".join(
        f'<span style="display:inline-block;margin:4px;padding:6px;background:{bg};color:{fg}">{escape(label)}</span>'
        for label, (bg, fg) in coverage_palette.items()
    )
    partial_html = (
        '<h2>Jurisdictions with one or more missing estimates</h2>'
        '<p>Each row is a jurisdiction and year. Red cells identify the missing estimates; '
        'green cells show which estimates are available.</p>'
        + legend + coverage_table_html(partial_coverage)
    )

    full_html = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Jurisdiction and year estimate coverage</title></head>'
        '<body style="font-family:Arial,sans-serif;margin:24px;color:#111827">'
        + partial_html
        + '<h2>All jurisdictions and years</h2>'
        + coverage_table_html(coverage)
        + '</body></html>'
    )
    (OUTPUT_DIR / "jurisdiction_year_coverage.html").write_text(full_html, encoding="utf-8")
    print(f"Saved coverage HTML; {len(partial_coverage)} jurisdiction-years have partial estimates.")

    # Per-estimate coverage: four cells per year for every jurisdiction.
    STATUS_ORDER = [
        "All estimates available", "Place not published in ACS 1-year",
        "One or more estimates missing", "2020 ACS 1-year not released",
    ]
    COLORS = ["#238b45", "#ef8a62", "#fdd76e", "#bdbdbd"]
    ESTIMATE_STATUSES = ["Available", "Missing estimate", "Place not published", "2020 not released"]
    ESTIMATE_COLORS = ["#238b45", "#dc3545", "#ef8a62", "#bdbdbd"]
    estimate_codes = {status: code for code, status in enumerate(ESTIMATE_STATUSES)}
    estimate_columns = [f"{metric}_status" for metric in METRICS]
    metric_letters = ["P", "R", "H", "W"]
    cmap = ListedColormap(ESTIMATE_COLORS)
    norm = BoundaryNorm(np.arange(-0.5, 4.5, 1), cmap.N)
    county_groups = list(roster.groupby("county_name", sort=True))
    row_heights = [max(len(group) for _, group in county_groups[start:start + 3]) for start in range(0, 9, 3)]
    fig, axes = plt.subplots(
        3, 3, figsize=(30, 23),
        gridspec_kw={"height_ratios": row_heights, "wspace": 0.6, "hspace": 0.42},
    )
    for county_index, (ax, (county_name, group)) in enumerate(zip(axes.flat, county_groups)):
        ordered = group.sort_values("jurisdiction_name")
        lookup = coverage.set_index(["GEOID", "year"])
        index = pd.MultiIndex.from_product([ordered["GEOID"], YEARS], names=["GEOID", "year"])
        statuses = lookup.reindex(index)[estimate_columns]
        assert statuses.notna().all().all(), "Unexpected missing coverage status"
        matrix = statuses.apply(lambda column: column.map(estimate_codes)).to_numpy().reshape(len(ordered), -1)
        assert matrix.shape == (len(ordered), len(YEARS) * len(METRICS))
        ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto", interpolation="nearest")
        # Keep cells the same height across each row of county panels.
        ax.set_ylim(row_heights[county_index // 3] - 0.5, -0.5)
        ax.set_xticks(range(len(YEARS) * 4), metric_letters * len(YEARS), fontsize=8)
        ax.set_yticks(range(len(ordered)), ordered["jurisdiction_name"], fontsize=10)
        ax.tick_params(axis="both", length=0, pad=5)
        year_axis = ax.secondary_xaxis("top")
        year_axis.set_xticks(np.arange(len(YEARS)) * 4 + 1.5, YEARS, fontsize=10)
        year_axis.tick_params(length=0, pad=6)
        ax.set_title(f"{county_name} ({len(ordered)} jurisdictions)", fontsize=14, pad=32, loc="left")
        for boundary in np.arange(-0.5, len(YEARS) * 4, 1):
            ax.vlines(boundary, -0.5, len(ordered) - 0.5, color="white", linewidth=0.35)
        for boundary in np.arange(-0.5, len(YEARS) * 4 + 1, 4):
            ax.vlines(boundary, -0.5, len(ordered) - 0.5, color="white", linewidth=2)
        for boundary in np.arange(-0.5, len(ordered), 1):
            ax.hlines(boundary, -0.5, len(YEARS) * 4 - 0.5, color="white", linewidth=0.5)
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.suptitle("Bay Area jurisdiction coverage by estimate, 2017–2023", y=0.985, fontsize=23)
    fig.text(
        0.5, 0.963,
        "Each year: P = Population    R = Resident workers    H = Work from home    W = Workplace workers",
        ha="center", fontsize=14,
    )
    fig.legend(
        handles=[Patch(facecolor=color, label=status) for status, color in zip(ESTIMATE_STATUSES, ESTIMATE_COLORS)],
        loc="lower center", ncol=4, frameon=False, fontsize=13, bbox_to_anchor=(0.5, 0.012),
    )
    fig.subplots_adjust(left=0.12, right=0.99, top=0.90, bottom=0.07)
    fig.savefig(OUTPUT_DIR / "jurisdiction_year_coverage.png", dpi=180, bbox_inches="tight")
    plt.close()

    missing = coverage.groupby("year")[estimate_columns].agg(lambda values: values.ne("Available").sum())
    ax = missing.plot.bar(figsize=(12, 5), rot=0)
    ax.set(title="Jurisdictions missing each ACS estimate", xlabel="Year", ylabel="Number of jurisdictions")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "missing_estimates_by_year.png", dpi=180, bbox_inches="tight")
    plt.close()

    ax = summary.reindex(columns=STATUS_ORDER, fill_value=0).plot.bar(
        stacked=True, color=COLORS, figsize=(11, 5), rot=0
    )
    ax.set(title="ACS 1-year availability by year", xlabel="Year", ylabel="Number of jurisdictions")
    ax.legend(title="Availability", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "coverage_summary_by_year.png", dpi=180, bbox_inches="tight")
    plt.close()


def plot_blockgroups(missing_pct, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ax = missing_pct.plot.barh(figsize=(11, 6))
    ax.set(title="ACS 2020-2024 block groups: estimate coverage by county",
           xlabel="Block groups missing estimate (%)", ylabel="County", xlim=(0, 105))
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(output_dir / "blockgroup_estimate_coverage_2020_2024.png", dpi=180, bbox_inches="tight")
    plt.close()
