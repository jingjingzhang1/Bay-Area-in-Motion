"""Tract resident population from the 2023 ACS 5-year table B01003 (2019-2023 period).

This is the fixed resident population P used in the tract daytime proxy (P + WAC - RAC).
Optionally checks it against MTC Vital Signs tract population, which publishes the
same ACS 5-year estimates.
"""
import io
import zipfile
from pathlib import Path

import pandas as pd

from src.utils.config import (
    BAY_AREA_COUNTIES, RAW_ACS5_TRACT_ZIP, RAW_VITAL_SIGNS_TRACTS, ACS_TRACT_POPULATION,
)

EXPECTED_TRACTS = 1772


def read_census_download(zip_path):
    """Read the '*-Data.csv' table inside a data.census.gov download (drops the label row)."""
    with zipfile.ZipFile(zip_path) as archive:
        name = next(n for n in archive.namelist() if n.endswith("-Data.csv"))
        with archive.open(name) as stream:
            frame = pd.read_csv(io.TextIOWrapper(stream, encoding="utf-8-sig"), dtype=str)
    if frame.iloc[0]["GEO_ID"] != "Geography":
        raise ValueError(f"Census label row not found in {zip_path}")
    return frame.iloc[1:].reset_index(drop=True)


def clean_acs_tract(zip_path=RAW_ACS5_TRACT_ZIP, output_path=ACS_TRACT_POPULATION,
                    vital_signs_path=RAW_VITAL_SIGNS_TRACTS):
    """Build one row per Bay Area tract with population, 90% MOE and reliability flags."""
    raw = read_census_download(zip_path)
    raw = raw[raw["GEO_ID"].str.startswith("1400000US")].copy()
    raw["tract_geoid"] = raw["GEO_ID"].str[-11:]
    raw["county_fips"] = raw["tract_geoid"].str[:5]
    tracts = raw[raw["county_fips"].isin(BAY_AREA_COUNTIES)].copy()
    tracts["county_name"] = tracts["county_fips"].map(BAY_AREA_COUNTIES)
    tracts["population"] = pd.to_numeric(tracts["B01003_001E"], errors="raise").astype(int)
    tracts["population_moe"] = pd.to_numeric(tracts["B01003_001M"], errors="coerce")
    if tracts["tract_geoid"].duplicated().any():
        raise ValueError("Duplicate tract GEOIDs in ACS download")
    if len(tracts) != EXPECTED_TRACTS:
        print(f"Warning: expected {EXPECTED_TRACTS} Bay Area tracts, found {len(tracts)}")

    pop = tracts["population"]
    tracts["population_relative_moe"] = (tracts["population_moe"] / pop.where(pop > 0)).round(5)
    tracts["flag_population_under_500"] = (pop < 500).astype(int)
    tracts["flag_relative_moe_gt_50pct"] = (tracts["population_relative_moe"] > 0.5).astype(int)
    columns = ["tract_geoid", "county_fips", "county_name", "population", "population_moe",
               "population_relative_moe", "flag_population_under_500", "flag_relative_moe_gt_50pct"]
    tracts = tracts[columns].sort_values("tract_geoid").reset_index(drop=True)

    if Path(vital_signs_path).exists():
        check_against_vital_signs(tracts, vital_signs_path)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    tracts.to_csv(output_path, index=False)
    print(f"Tract ACS: {len(tracts)} tracts saved to {Path(output_path).name} "
          f"({int((tracts.population == 0).sum())} with zero population, mostly water tracts)")
    return tracts


def check_against_vital_signs(tracts, vital_signs_path):
    """Confirm the Vital Signs 2023 tract population equals the ACS 5-year estimate."""
    vital = pd.read_csv(vital_signs_path, dtype={"tract_geoid": str})
    merged = vital[["tract_geoid", "population_2023"]].merge(tracts, on="tract_geoid", how="left")
    missing = merged["population"].isna().sum()
    mismatched = (pd.to_numeric(merged["population_2023"]) != merged["population"]).sum() - missing
    print(f"Vital Signs check: {len(vital)} tracts, {missing} not in ACS, {mismatched} population mismatches")
    return mismatched
