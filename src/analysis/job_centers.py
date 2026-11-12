
import numpy as np
import pandas as pd

from src.utils.config import WAC_RAC_TRACTS, TABLES_DIR


def classify_job_centers(df):
    """Classify Bay Area tracts using workplace and residence jobs."""
    df = df.copy()

    total_jobs = df["WAC"] + df["RAC"]

    # Balance index ranges from -1 to 1.
    df["balance_index"] = (
        (df["WAC"] - df["RAC"]) /
        total_jobs.replace(0, np.nan)
    )

    # Workplace-to-residence jobs ratio.
    df["job_residence_ratio"] = (
        df["WAC"] / df["RAC"].replace(0, np.nan)
    )
    df.loc[
        (df["RAC"] == 0) & (df["WAC"] > 0),
        "job_residence_ratio"
    ] = np.inf

    # Preliminary thresholds; sensitivity testing comes in CK1b.
    ratio = df["job_residence_ratio"]
    df["tract_type"] = np.select(
        [
            ratio >= 1.25,
            ratio <= 0.80,
            ratio.between(0.80, 1.25, inclusive="neither")
        ],
        ["Job Center", "Bedroom Community", "Balanced Area"],
        default="No jobs recorded"
    )

    return df


def main():
    df = pd.read_csv(
        WAC_RAC_TRACTS,
        dtype={"tract_geoid": str, "county_fips": str}
    )

    result = classify_job_centers(df)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    output = TABLES_DIR / "ck1a_job_center_typology.csv"
    result.to_csv(output, index=False)

    print(result.groupby(["year", "tract_type"]).size())
    print("Saved:", output)


if __name__ == "__main__":
    main()
