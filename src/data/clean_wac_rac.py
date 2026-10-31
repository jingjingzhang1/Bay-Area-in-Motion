"""Clean LODES WAC (jobs by workplace) and RAC (jobs by residence) into one tract table.

Output: one row per Bay Area tract and year with WAC, RAC and net_change = WAC - RAC.
Same layout as the team's cleaned file (Happy's notebook): about 1,765 tracts x 7 years.
Only all-jobs totals (C000) for primary jobs (JT01) are used.
"""
from pathlib import Path

import pandas as pd

from src.utils.config import BAY_AREA_COUNTIES, RAW_DIR, WAC_RAC_TRACTS

RAW_PATTERN = "ca_{kind}_S000_JT01_{year}.csv.gz"   # in data/raw/lodes/


def raw_wac_rac_path(kind, year):
    return RAW_DIR / "lodes" / RAW_PATTERN.format(kind=kind, year=year)


def tract_totals(kind, year):
    """Sum C000 jobs from blocks to 2020 tracts for one file; keep Bay Area tracts only."""
    geo = "w_geocode" if kind == "wac" else "h_geocode"
    raw = pd.read_csv(raw_wac_rac_path(kind, year), usecols=[geo, "C000"], dtype={geo: str})
    raw["tract_geoid"] = raw[geo].str[:11]
    raw = raw[raw["tract_geoid"].str[:5].isin(BAY_AREA_COUNTIES)]
    return raw.groupby("tract_geoid")["C000"].sum().rename(kind.upper()), len(raw)


def clean_wac_rac(years, output_path=WAC_RAC_TRACTS):
    """Build the tract WAC/RAC table for all years and save it. Returns (table, row_log)."""
    frames, log = [], []
    for year in years:
        if not (raw_wac_rac_path("wac", year).exists() and raw_wac_rac_path("rac", year).exists()):
            print(f"MISSING raw WAC/RAC files for {year}")
            continue
        wac, wac_blocks = tract_totals("wac", year)
        rac, rac_blocks = tract_totals("rac", year)
        tracts = pd.concat([wac, rac], axis=1).fillna(0).astype(int).reset_index()
        tracts["net_change"] = tracts["WAC"] - tracts["RAC"]
        tracts["year"] = year
        tracts["county_fips"] = tracts["tract_geoid"].str[:5]
        frames.append(tracts)
        log.append({"year": year, "wac_bay_blocks": wac_blocks, "rac_bay_blocks": rac_blocks,
                    "tracts": len(tracts)})
    if not frames:
        return None, pd.DataFrame(log)
    table = pd.concat(frames, ignore_index=True)[["tract_geoid", "WAC", "RAC", "net_change", "year", "county_fips"]]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output_path, index=False)
    print(f"WAC/RAC: {len(table):,} tract-year rows saved to {Path(output_path).name}")
    return table, pd.DataFrame(log)
