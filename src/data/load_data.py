"""Read raw and cleaned files. Geographic IDs are always read as text to keep leading zeros."""
import pandas as pd

from src.utils.config import (
    RAW_XWALK, WAC_RAC_TRACTS, ACS_COUNTY, BAY_AREA_COUNTIES, od_path,
)

OD_ID_COLS = {"h_county": str, "w_county": str, "h_tract": str, "w_tract": str}


def load_raw_crosswalk(path=RAW_XWALK):
    """LODES block crosswalk, only the columns we use."""
    return pd.read_csv(path, dtype=str, usecols=["tabblk2020", "cty", "ctyname", "trct"])


def iter_od(year, chunksize=1_000_000):
    """Yield chunks of one cleaned OD year with only the columns needed for analysis."""
    return pd.read_csv(od_path(year), usecols=list(OD_ID_COLS) + ["S000"],
                       dtype=OD_ID_COLS, chunksize=chunksize)


def load_wac_rac(path=WAC_RAC_TRACTS):
    """Cleaned tract WAC/RAC table: tract_geoid, county_fips, year, WAC, RAC, net_change."""
    frame = pd.read_csv(path, dtype={"tract_geoid": str, "county_fips": str})
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    return frame


def load_acs_county(path=ACS_COUNTY):
    """Cleaned county ACS 1-year panel (one row per county and year)."""
    frame = pd.read_csv(path, dtype={"county_fips": str})
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    if not frame["county_fips"].isin(BAY_AREA_COUNTIES).all():
        raise ValueError(f"Expected five-digit Bay Area county FIPS codes in {path}")
    if frame.duplicated(["year", "county_fips"]).any():
        raise ValueError(f"Duplicate county-year estimates in {path}")
    return frame
