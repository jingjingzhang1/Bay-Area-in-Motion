
"""CK1b: Job center classification sensitivity analysis, 2017-2023."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/processed/lodes_wac_rac_tracts_2017_2023.csv"
TABLES = ROOT / "outputs/tables"
FIGURES = ROOT / "outputs/figures"

SCENARIOS = {
    "Lenient": (1.10, 0.90),
    "Baseline": (1.25, 0.80),
    "Strict": (1.50, 0.67),
}


def classify(df, job_threshold, bedroom_threshold):
    """Classify each tract by its workplace/residence job ratio."""
    wac = df["WAC"]
    rac = df["RAC"]

    no_jobs = (wac == 0) & (rac == 0)

    ratio = wac.div(rac.replace(0, np.nan))
    ratio = ratio.mask((rac == 0) & (wac > 0), np.inf)

    return pd.Series(
        np.select(
            [
                no_jobs,
                ratio >= job_threshold,
                ratio <= bedroom_threshold,
            ],
            [
                "No jobs recorded",
                "Job Center",
                "Bedroom Community",
            ],
            default="Balanced Area",
        ),
        index=df.index,
    )


def main():
    df = pd.read_csv(
        DATA,
        dtype={"tract_geoid": str, "county_fips": str},
    )

    df = df[df["year"].between(2017, 2023)].copy()

    if df.duplicated(["tract_geoid", "year"]).any():
        raise ValueError("Duplicate tract-year records found")

    for col in ["WAC", "RAC"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if df[["WAC", "RAC"]].isna().any().any():
        raise ValueError("Missing or invalid WAC/RAC values")

    if (df[["WAC", "RAC"]] < 0).any().any():
        raise ValueError("Negative WAC/RAC values found")

    # Original CK1a classification
    baseline = classify(df, 1.25, 0.80)

    results = []

    for scenario, (job_cutoff, bedroom_cutoff) in SCENARIOS.items():
        labels = classify(df, job_cutoff, bedroom_cutoff)

        temp = df[["tract_geoid", "year"]].copy()
        temp["tract_type"] = labels
        temp["changed_from_baseline"] = labels != baseline

        for year, group in temp.groupby("year"):
            total = len(group)
            counts = group["tract_type"].value_counts()

            job_count = int(counts.get("Job Center", 0))
            bedroom_count = int(counts.get("Bedroom Community", 0))
            balanced_count = int(counts.get("Balanced Area", 0))
            no_jobs_count = int(counts.get("No jobs recorded", 0))
            changed_count = int(group["changed_from_baseline"].sum())

            results.append({
                "year": year,
                "scenario": scenario,
                "job_threshold": job_cutoff,
                "bedroom_threshold": bedroom_cutoff,
                "total_tracts": total,
                "job_centers": job_count,
                "bedroom_communities": bedroom_count,
                "balanced_areas": balanced_count,
                "no_jobs_recorded": no_jobs_count,
                "job_center_share_pct": 100 * job_count / total,
                "reclassified_tracts": changed_count,
                "reclassified_pct": 100 * changed_count / total,
            })

    result = pd.DataFrame(results)
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    result.to_csv(
        TABLES / "ck1b_sensitivity_summary.csv",
        index=False,
    )

    # Figure: share of tracts classified as job centers
    fig, ax = plt.subplots(figsize=(10, 6))

    for scenario in SCENARIOS:
        subset = result[result["scenario"] == scenario]
        ax.plot(
            subset["year"],
            subset["job_center_share_pct"],
            marker="o",
            linewidth=2,
            label=scenario,
        )

    ax.set_title(
        "Sensitivity of Job Center Classification\n"
        "Bay Area Census Tracts, 2017-2023"
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("Census Tracts Classified as Job Centers (%)")
    ax.set_xticks(range(2017, 2024))
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.25)
    ax.legend(title="Threshold Scenario")

    fig.text(
        0.5, 0.01,
        "Source: LEHD LODES8 WAC/RAC. "
        "Scenarios use different WAC/RAC thresholds.",
        ha="center",
        fontsize=9,
    )

    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(
        FIGURES / "fig_ck1b_job_center_sensitivity.png",
        dpi=200,
    )
    plt.close(fig)

    print("\n=== CK1b: Job Center Sensitivity ===")
    print(
        result[result["year"].isin([2017, 2023])][
            [
                "year",
                "scenario",
                "job_centers",
                "job_center_share_pct",
                "reclassified_tracts",
            ]
        ].to_string(index=False)
    )

    print("\nCK1b sensitivity analysis saved")


if __name__ == "__main__":
    main()
