"""Functions to clean and prepare data."""
import pandas as pd

from src.utils.config import BAY_AREA_COUNTIES, CHUNK_ROWS, PROCESSED_DIR
from src.data.load_data import load_crosswalk, raw_od_path, processed_od_path


def clean_crosswalk():
    """Keep only Bay Area blocks from the crosswalk and save it. Returns the cleaned table."""
    xwalk = load_crosswalk()
    raw_rows = len(xwalk)
    xwalk = xwalk.dropna(subset=["tabblk2020"]).drop_duplicates()
    xwalk_bay = xwalk[xwalk["cty"].isin(BAY_AREA_COUNTIES)].copy()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    xwalk_bay.to_csv(PROCESSED_DIR / "ca_xwalk.csv.gz", index=False, compression="gzip")
    print(f"Crosswalk: {raw_rows:,} raw rows, {len(xwalk_bay):,} Bay Area rows kept")
    return xwalk_bay


def clean_od_year(year):
    """Filter one year of OD data to commutes with home OR work in the Bay Area.

    Adds county codes, county names and tract IDs (first 11 digits of the block ID),
    drops duplicates and saves the result. Skips years already processed.
    Returns (raw_rows, kept_rows), or None if skipped or the raw file is missing.
    """
    in_path, out_path = raw_od_path(year), processed_od_path(year)
    if out_path.exists():
        print(f"Skipping {out_path.name} (already processed)")
        return None
    if not in_path.exists():
        print(f"MISSING raw file {in_path.name}: download it into data/raw first")
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
    """Run clean_od_year for every year."""
    for year in years:
        clean_od_year(year)
