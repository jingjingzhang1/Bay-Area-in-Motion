"""Clean the LODES crosswalk and origin-destination (OD) files."""
import pandas as pd

from src.utils.config import (
    BAY_AREA_COUNTIES, CHUNK_ROWS, PROCESSED_DIR, XWALK_BAY, raw_od_path, od_path,
)
from src.utils.helpers import count_rows
from src.data.load_data import load_raw_crosswalk


def clean_crosswalk():
    """Keep only Bay Area blocks from the crosswalk and save them. Returns the cleaned table."""
    xwalk = load_raw_crosswalk()
    raw_rows = len(xwalk)
    xwalk = xwalk.dropna(subset=["tabblk2020"]).drop_duplicates()
    xwalk_bay = xwalk[xwalk["cty"].isin(BAY_AREA_COUNTIES)].copy()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    xwalk_bay.to_csv(XWALK_BAY, index=False, compression="gzip")
    print(f"Crosswalk: {raw_rows:,} raw rows, {len(xwalk_bay):,} Bay Area rows kept")
    return xwalk_bay


def clean_od_year(year):
    """Keep one year of OD commutes whose home OR work block is in the Bay Area.

    Adds county codes, county names and tract IDs (first 11 digits of the 2020 block ID),
    drops duplicates and saves the result. Skips years already cleaned.
    Returns (raw_rows, kept_rows), or None when skipped or the raw file is missing.
    """
    in_path, out_path = raw_od_path(year), od_path(year)
    if out_path.exists():
        print(f"Skipping {out_path.name} (already cleaned)")
        return None
    if not in_path.exists():
        print(f"MISSING raw file {in_path}: download it first (see README)")
        return None

    bay_fips = set(BAY_AREA_COUNTIES)
    kept, n_raw = [], 0
    for chunk in pd.read_csv(in_path, dtype={"w_geocode": str, "h_geocode": str}, chunksize=CHUNK_ROWS):
        n_raw += len(chunk)
        chunk = chunk.dropna(subset=["w_geocode", "h_geocode"])
        chunk["h_county"] = chunk["h_geocode"].str[:5]
        chunk["w_county"] = chunk["w_geocode"].str[:5]
        chunk = chunk[chunk["h_county"].isin(bay_fips) | chunk["w_county"].isin(bay_fips)].copy()
        chunk["h_county_name"] = chunk["h_county"].map(BAY_AREA_COUNTIES).fillna("Outside Bay Area")
        chunk["w_county_name"] = chunk["w_county"].map(BAY_AREA_COUNTIES).fillna("Outside Bay Area")
        chunk["h_tract"] = chunk["h_geocode"].str[:11]
        chunk["w_tract"] = chunk["w_geocode"].str[:11]
        kept.append(chunk)

    df = pd.concat(kept, ignore_index=True).drop_duplicates()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, compression="gzip")
    print(f"{in_path.name}: {n_raw:,} raw rows, {len(df):,} kept")
    return n_raw, len(df)


def clean_od(years):
    """Clean every OD year."""
    for year in years:
        clean_od_year(year)


def od_row_log(years, log_file):
    """Raw vs kept row counts for each OD year (reported in the Data section)."""
    log = pd.read_csv(log_file) if log_file.exists() else pd.DataFrame(columns=["year", "raw_rows", "kept_rows"])
    for year in years:
        if year in log["year"].values or not raw_od_path(year).exists() or not od_path(year).exists():
            continue
        log.loc[len(log)] = [year, count_rows(raw_od_path(year)), count_rows(od_path(year))]
    log = log.sort_values("year").reset_index(drop=True)
    log["kept_pct"] = (log["kept_rows"].astype(float) / log["raw_rows"].astype(float) * 100).round(1)
    log.to_csv(log_file, index=False)
    return log
