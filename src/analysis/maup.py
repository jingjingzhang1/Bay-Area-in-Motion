
"""CK3: Compare net-job changes at county, city, and tract scales."""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "outputs" / "tables"
TRACT_FILE = ROOT / "data" / "processed" / "lodes_wac_rac_tracts_2017_2023.csv"


def compare_scale(df, scale, id_col, jobs_col, name_col=None):
    """Calculate 2017–2023 change for units observed in both years."""
    df = df[df["year"].isin([2017, 2023])].copy()

    if name_col:
        df["unit_name"] = df[name_col].astype(str)
    else:
        df["unit_name"] = df[id_col].astype(str)

    counts = df.groupby([id_col, "year"]).size()
    if (counts > 1).any():
        raise ValueError(f"Duplicate {scale} IDs and years")

    wide = df.pivot(
        index=id_col,
        columns="year",
        values=jobs_col
    ).dropna(subset=[2017, 2023])

    names = df.drop_duplicates(id_col).set_index(id_col)["unit_name"]

    result = pd.DataFrame({
        "scale": scale,
        "unit_id": wide.index.astype(str),
        "unit_name": names.reindex(wide.index).values,
        "net_jobs_2017": wide[2017].values,
        "net_jobs_2023": wide[2023].values,
    })

    result["delta_net_jobs"] = (
        result["net_jobs_2023"] - result["net_jobs_2017"]
    )
    return result


def main():
    county = pd.read_csv(
        TABLES / "daytime_county.csv",
        dtype={"county_fips": str}
    )
    city = pd.read_csv(
        TABLES / "hy2a_city_2017_2023.csv",
        dtype={"GEOID": str}
    )
    tract = pd.read_csv(
        TRACT_FILE,
        dtype={"tract_geoid": str}
    )

    county_result = compare_scale(
        county, "County", "county_fips",
        "net_jobs", "county_name"
    )
    city_result = compare_scale(
        city, "City", "GEOID",
        "net_jobs", "jurisdiction_name"
    )
    tract_result = compare_scale(
        tract, "Tract", "tract_geoid",
        "net_change"
    )

    all_results = pd.concat(
        [county_result, city_result, tract_result],
        ignore_index=True
    )

    summary = all_results.groupby("scale").agg(
        units=("unit_id", "count"),
        median_abs_change=("delta_net_jobs", lambda s: s.abs().median()),
        largest_gain=("delta_net_jobs", "max"),
        largest_loss=("delta_net_jobs", "min"),
    )

    TABLES.mkdir(parents=True, exist_ok=True)
    all_results.to_csv(TABLES / "maup_scale_comparison.csv", index=False)
    summary.to_csv(TABLES / "maup_summary.csv")

    # CK3: Compare the scale of net-job changes
    fig, ax = plt.subplots(figsize=(9, 5))

    order = ["Tract", "City", "County"]
    values = summary.loc[order, "median_abs_change"]

    bars = ax.bar(order, values)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:,.0f}",
            ha="center",
            va="bottom"
        )

    ax.set_title(
        "Median Absolute Change in Net Jobs by Geographic Scale\n"
        "Bay Area, 2017–2023"
    )
    ax.set_xlabel("Geographic Scale")
    ax.set_ylabel("Median Absolute Change (jobs)")

    fig.text(
        0.5, 0.01,
        "Source: LEHD LODES8 WAC/RAC. Unnormalized values; "
        "geographic units differ in size.",
        ha="center",
        fontsize=9
    )

    fig.tight_layout(rect=[0, 0.06, 1, 1])

    figures_dir = ROOT / "outputs" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    fig.savefig(
        figures_dir / "fig_ck3_maup_scale_comparison.png",
        dpi=200
    )
    plt.close(fig)

    print(summary)
    print("CK3: MAUP comparison saved")


if __name__ == "__main__":
    main()
