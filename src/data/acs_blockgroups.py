"""ACS 2020-2024 block-group estimates, margins of error and annotations."""
import numpy as np
import pandas as pd
from pathlib import Path

from src.data.census_api import COUNTIES, STATE, VARIABLES, METRICS, CensusClient
from src.utils.config import PROCESSED_DIR

RELEASE_YEAR = 2024
YEARS = [RELEASE_YEAR]
# Request estimates, MOEs, and both annotations; raw negative sentinel values stay in the cache.
api_columns = {}
for variable, metric in VARIABLES.items():
    stem = variable[:-1]
    api_columns.update({
        variable: metric, stem + "M": metric + "_moe",
        stem + "EA": metric + "_annotation", stem + "MA": metric + "_moe_annotation",
    })


def run(output_dir=PROCESSED_DIR / "acs5_blockgroup_output", *, client=None, force_refresh=False):
    OUTPUT_DIR = Path(output_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client = client or CensusClient(OUTPUT_DIR / "api_cache", force_refresh)
    def query_blockgroups(year, county):
        url = f"https://api.census.gov/data/{year}/acs/acs5"
        params = {
            "get": "NAME," + ",".join(api_columns),
            "for": "block group:*",
            "in": f"state:{STATE} county:{county} tract:*",
        }
        frame = client.table(year, "acs/acs5", params).rename(columns=api_columns)
        frame["year"] = year
        frame["period_start"] = year - 4
        frame["period_end"] = year
        frame["estimate_period"] = f"{year - 4}–{year}"
        frame["county_name"] = COUNTIES[county]
        frame = frame.rename(columns={"block group": "block_group"})
        frame["county_fips"] = frame["state"] + frame["county"]
        frame["tract_geoid"] = frame["county_fips"] + frame["tract"]
        frame["GEOID"] = frame["tract_geoid"] + frame["block_group"]
        for metric in METRICS:
            for column in [metric, metric + "_moe"]:
                numeric = pd.to_numeric(frame[column], errors="coerce")
                frame[column] = numeric.mask(numeric < 0)
        assert frame["GEOID"].str.len().eq(12).all()
        assert frame["county"].eq(county).all()
        assert not frame.duplicated("GEOID").any()
        return frame

    frames = []
    for year in YEARS:
        for county, county_name in COUNTIES.items():
            frame = query_blockgroups(year, county)
            frames.append(frame)
            print(f"{year} ({year - 4}–{year}), {county_name}: {len(frame):,} block groups")
    blockgroups = pd.concat(frames, ignore_index=True)
    blockgroups["work_from_home_pct"] = (
        100 * blockgroups["work_from_home"]
        / blockgroups["workers_residence"].where(blockgroups["workers_residence"] > 0)
    )
    # This derived percentage has no calculated MOE; count MOEs are provided separately.
    blockgroups["missing_metrics"] = blockgroups[METRICS].apply(
        lambda row: "; ".join(row.index[row.isna()]), axis=1
    )
    blockgroups["availability"] = np.select(
        [blockgroups[METRICS].isna().all(axis=1), blockgroups[METRICS].isna().any(axis=1)],
        ["All estimates missing", "One or more estimates missing"], default="All estimates available",
    )
    blockgroups = blockgroups.sort_values(["year", "GEOID"]).reset_index(drop=True)
    assert not blockgroups.duplicated(["year", "GEOID"]).any()
    assert set(blockgroups["year"]) == set(YEARS)
    assert len(blockgroups.groupby(["year", "county"])) == len(YEARS) * len(COUNTIES)
    print(f"Total: {len(blockgroups):,} block-group/release records.")

    identity = [
        "year", "period_start", "period_end", "estimate_period", "GEOID",
        "state", "county", "county_fips", "county_name", "tract", "tract_geoid", "block_group", "NAME",
    ]
    blockgroups = blockgroups[identity + list(api_columns.values()) + ["work_from_home_pct", "availability", "missing_metrics"]]
    blockgroups.to_csv(OUTPUT_DIR / "bay_area_acs5_blockgroups_2020_2024.csv", index=False)
    for table, metrics in {
        "population": ["population"],
        "B08301": ["workers_residence", "work_from_home"],
        "B08604": ["workers_workplace"],
    }.items():
        columns = identity + [column for metric in metrics for column in
            [metric, metric + "_moe", metric + "_annotation", metric + "_moe_annotation"]]
        if table == "B08301":
            columns += ["work_from_home_pct"]
        blockgroups[columns].to_csv(OUTPUT_DIR / f"bay_area_acs5_blockgroups_{table}_2020_2024.csv", index=False)

    coverage = blockgroups[identity + ["availability", "missing_metrics"]].copy()
    for metric in METRICS:
        coverage[f"{metric}_status"] = np.where(blockgroups[metric].notna(), "Available", "Missing estimate")
        coverage[f"{metric}_annotation"] = blockgroups[f"{metric}_annotation"]
    coverage.to_csv(OUTPUT_DIR / "blockgroup_coverage_2020_2024.csv", index=False)
    coverage.loc[coverage["missing_metrics"].ne("")].to_csv(
        OUTPUT_DIR / "missing_blockgroups_2020_2024.csv", index=False
    )
    counts = blockgroups.groupby("county_name").size().rename("block_groups")
    counts.to_csv(OUTPUT_DIR / "blockgroup_counts_by_county_2020_2024.csv")
    missing_counts = blockgroups.groupby("county_name")[METRICS].agg(lambda values: values.isna().sum())
    missing_pct = missing_counts.div(counts, axis=0) * 100
    missing_counts.to_csv(OUTPUT_DIR / "missing_estimates_by_county_2020_2024.csv")
    missing_pct.to_csv(OUTPUT_DIR / "missing_estimates_pct_by_county_2020_2024.csv")

    return blockgroups, coverage, missing_pct
