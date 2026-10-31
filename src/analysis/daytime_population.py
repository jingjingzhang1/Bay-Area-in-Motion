"""County daytime population proxies from the original merge notebook."""
import pandas as pd

from src.data.census_api import clean_counts
from src.utils.config import BAY_AREA_COUNTIES


def read_county_estimates(path, values):
    frame = pd.read_csv(path, dtype={"GEOID": str})
    frame = frame[["year", "GEOID"] + values].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    if not frame["GEOID"].isin(BAY_AREA_COUNTIES).all():
        raise ValueError(f"Expected five-digit Bay Area county GEOIDs in {path}")
    if frame.duplicated(["year", "GEOID"]).any():
        raise ValueError(f"Duplicate county-year estimates in {path}")
    return clean_counts(frame, values)


def merge_counties(lodes_path, population_path, residence_path, workplace_path):
    """Keep every input LODES county-year, including 2020 with missing ACS.

    The input is already cleaned tract WAC/RAC; its upstream cleaning notebook
    was not present in the local handoff. No missing job counts become zero.
    """
    lodes = pd.read_csv(lodes_path, dtype={"tract_geoid": str, "county_fips": str})
    required = ["year", "tract_geoid", "county_fips", "WAC", "RAC"]
    lodes = lodes[required].copy()
    lodes["year"] = pd.to_numeric(lodes["year"], errors="raise").astype(int)
    if (not lodes["county_fips"].isin(BAY_AREA_COUNTIES).all()
            or not lodes["tract_geoid"].str.fullmatch(r"\d{11}").fillna(False).all()
            or not lodes["tract_geoid"].str[:5].eq(lodes["county_fips"]).all()):
        raise ValueError("Invalid Bay Area tract/county identifiers in LODES input")
    if lodes.duplicated(["year", "tract_geoid"]).any():
        raise ValueError("Duplicate tract-year rows in LODES input")
    for column in ["WAC", "RAC"]:
        lodes[column] = pd.to_numeric(lodes[column], errors="raise")
        if lodes[column].isna().any() or (lodes[column] < 0).any():
            raise ValueError(f"Missing or negative {column} jobs")
    county = lodes.groupby(["year", "county_fips"], as_index=False)[["WAC", "RAC"]].sum()
    county["GEOID"] = county["county_fips"]
    for path, values in [
        (population_path, ["population"]),
        (residence_path, ["workers_residence", "work_from_home"]),
        (workplace_path, ["workers_workplace"]),
    ]:
        county = county.merge(read_county_estimates(path, values),
                              on=["year", "GEOID"], how="left", validate="one_to_one")
    # Even a stale input file must not supply standard ACS 1-year values for 2020.
    acs_columns = ["population", "workers_residence", "work_from_home", "workers_workplace"]
    county.loc[county["year"].eq(2020), acs_columns] = float("nan")
    county["county_name"] = county["county_fips"].map(BAY_AREA_COUNTIES)
    county["net_change"] = county["WAC"] - county["RAC"]
    county["daytime_population_LODES"] = county["population"] + county["net_change"]
    county["daytime_population_acs"] = county["population"] + county["workers_workplace"] - county["workers_residence"]
    county["daytime_population_difference_2_metrics"] = county["daytime_population_LODES"] - county["daytime_population_acs"]
    county["work_from_home_pct"] = 100 * county["work_from_home"] / county["workers_residence"].where(county["workers_residence"] > 0)
    columns = ["year", "county_fips", "county_name", "population", "WAC", "RAC", "net_change",
               "daytime_population_LODES", "workers_residence", "workers_workplace", "work_from_home",
               "work_from_home_pct", "daytime_population_acs", "daytime_population_difference_2_metrics"]
    return county[columns].sort_values(["year", "county_name"]).reset_index(drop=True)
