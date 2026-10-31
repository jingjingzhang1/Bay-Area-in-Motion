"""County ACS 1-year panel: population, resident workers, work from home and workplace workers.

One table, one row per county and year (2017-2024), with 90% margins of error.
Downloaded from the Census API, so no manual download is needed.
"""
from pathlib import Path

import pandas as pd

from src.data.census_api import (
    COUNTIES, STATE, VARIABLES, MOE_VARIABLES, METRICS, CensusClient, clean_counts, add_coverage,
)
from src.utils.config import ACS_COUNTY, CENSUS_CACHE_DIR

ACS_COUNTY_YEARS = [year for year in range(2017, 2025) if year != 2020]
MOE_COLUMNS = list(MOE_VARIABLES.values())


def clean_acs_county(output_path=ACS_COUNTY, *, client=None, force_refresh=False):
    """Download and clean the county panel; save it to output_path and return it.

    - 2020 is skipped: there is no standard ACS 1-year release for 2020.
    - Negative Census sentinel codes become missing, never zero
      (e.g. Napa B08301 in 2021-2022, and every B01003 MOE because population is a
      controlled estimate with no numeric MOE).
    - A failed request stops the run instead of becoming a missing estimate.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    client = client or CensusClient(CENSUS_CACHE_DIR / "county", force_refresh)
    variables = {**VARIABLES, **MOE_VARIABLES}
    frames = []
    for year in ACS_COUNTY_YEARS:
        for county, county_name in COUNTIES.items():
            frame = client.table(year, "acs/acs1", {
                "get": "NAME," + ",".join(variables),
                "for": f"county:{county}", "in": f"state:{STATE}",
            }).rename(columns=variables)
            if len(frame) != 1 or not frame["state"].eq(STATE).all() or not frame["county"].eq(county).all():
                raise ValueError(f"Unexpected county geography: {year}, {county}")
            frame["county_fips"] = frame["state"] + frame["county"]
            frame["county_name"] = county_name
            frame["year"] = year
            clean_counts(frame, list(variables.values()))
            frames.append(frame)
    panel = add_coverage(pd.concat(frames, ignore_index=True))
    if panel.duplicated(["year", "county_fips"]).any():
        raise ValueError("Duplicate county-year estimates")
    columns = ["year", "county_fips", "county_name"] + METRICS + ["work_from_home_pct"] + MOE_COLUMNS + ["missing_metrics"]
    panel = panel[columns].sort_values(["year", "county_fips"]).reset_index(drop=True)
    panel.to_csv(output_path, index=False)
    print(f"County ACS: {len(panel)} county-year rows saved to {output_path.name}")
    return panel
