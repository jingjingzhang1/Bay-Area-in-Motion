"""County ACS exports used by the existing OD analysis and daytime comparison."""
from pathlib import Path

import pandas as pd

from src.data.census_api import COUNTIES, STATE, VARIABLES, CensusClient, clean_counts, add_coverage
from src.utils.config import PROCESSED_DIR

POPULATION_FILE = "bay_area_acs1_population_2017_2024.csv"
RESIDENCE_FILE = "bay_area_acs1_B08301_workers_by_where_they_live_and_working_from_home_2018_2024.csv"
WORKPLACE_FILE = "bay_area_acs1_B08604_workers_by_workplace_2018_2024.csv"


def run(output_dir=PROCESSED_DIR, *, client=None, force_refresh=False):
    """Preserve the original population/residence 2017 start and workplace 2018 start.

    No standard ACS 1-year estimates are requested for 2020. Historical worker
    filenames are retained for compatibility with src.main; residence includes 2017.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    client = client or CensusClient(output_dir / "acs_county_cache", force_refresh)
    frames = []
    for year in range(2017, 2025):
        if year == 2020:
            continue
        variables = {key: value for key, value in VARIABLES.items()
                     if year >= 2018 or value != "workers_workplace"}
        for county, county_name in COUNTIES.items():
            frame = client.table(year, "acs/acs1", {
                "get": "NAME," + ",".join(variables),
                "for": f"county:{county}", "in": f"state:{STATE}",
            }).rename(columns=variables)
            if len(frame) != 1 or not frame["state"].eq(STATE).all() or not frame["county"].eq(county).all():
                raise ValueError(f"Unexpected county geography: {year}, {county}")
            frame["GEOID"] = frame["state"] + frame["county"]
            frame["year"] = year
            frame["county_name"] = county_name
            clean_counts(frame, variables.values())
            frames.append(frame)
    panel = add_coverage(pd.concat(frames, ignore_index=True))
    if panel.duplicated(["year", "GEOID"]).any():
        raise ValueError("Duplicate county-year estimates")
    identity = ["year", "GEOID", "county_name", "NAME"]
    panel[identity + ["population"]].to_csv(output_dir / POPULATION_FILE, index=False)
    panel[identity + ["workers_residence", "work_from_home", "work_from_home_pct"]].to_csv(
        output_dir / RESIDENCE_FILE, index=False
    )
    panel.loc[panel["year"].ge(2018), identity + ["workers_workplace"]].to_csv(
        output_dir / WORKPLACE_FILE, index=False
    )
    return panel
