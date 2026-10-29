"""Functions to read data files. IDs are always read as text to keep leading zeros."""
import pandas as pd

from src.utils.config import RAW_DIR, PROCESSED_DIR

ID_COLS = {"h_county": str, "w_county": str, "h_tract": str, "w_tract": str}


def raw_od_path(year):
    return RAW_DIR / f"ca_od_main_JT01_{year}.csv.gz"


def processed_od_path(year):
    return PROCESSED_DIR / f"ca_od_main_JT01_{year}.csv.gz"


def load_crosswalk():
    """Read the LODES block crosswalk (only the columns we use)."""
    return pd.read_csv(
        RAW_DIR / "ca_xwalk.csv.gz",
        dtype=str,
        usecols=["tabblk2020", "cty", "ctyname", "trct"],
    )


def iter_processed_od(year, chunksize=1_000_000):
    """Yield chunks of a processed OD file with only the columns needed for analysis."""
    return pd.read_csv(
        processed_od_path(year),
        usecols=list(ID_COLS) + ["S000"],
        dtype=ID_COLS,
        chunksize=chunksize,
    )


def load_wac_rac(path):
    """Read the cleaned tract-level WAC/RAC table (tract_geoid, WAC, RAC, net_change, year, county_fips)."""
    return pd.read_csv(path, dtype={"tract_geoid": str, "county_fips": str})


def load_acs_workers(res_path, work_path):
    """Combine ACS B08301 (workers by residence) and B08604 (workers by workplace) by county and year."""
    res = pd.read_csv(res_path, dtype={"GEOID": str})[["year", "GEOID", "workers_residence"]]
    wk = pd.read_csv(work_path, dtype={"GEOID": str})[["year", "GEOID", "workers_workplace"]]
    acs = res.merge(wk, on=["year", "GEOID"])
    acs = acs.rename(columns={
        "GEOID": "county",
        "workers_residence": "workers_by_residence",
        "workers_workplace": "workers_by_workplace",
    })
    acs["county"] = acs["county"].str.zfill(5)
    return acs
