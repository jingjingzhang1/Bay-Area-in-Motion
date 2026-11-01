"""TIGER/Line 2020 boundaries and the tract-to-city spatial join.

Spatial join: each 2020 census tract is assigned to the 2020 place (city or CDP) that
contains the tract's internal point (a point guaranteed to fall inside the tract).
Tracts whose internal point is in no place are unincorporated. This lets tract data
(WAC/RAC, population) be summed to cities, the middle geographic scale of the project.
"""
from pathlib import Path

import pandas as pd

from src.utils.config import (
    BAY_AREA_COUNTIES, RAW_DIR, PROJECT_CRS, TIGER_TRACTS, TRACT_TO_PLACE,
)

TIGER_BASE = "https://www2.census.gov/geo/tiger/TIGER2020"
TRACT_ZIP = RAW_DIR / "tiger" / "tl_2020_06_tract.zip"
PLACE_ZIP = RAW_DIR / "tiger" / "tl_2020_06_place.zip"


def download_tiger(zip_path, url):
    """Download a TIGER zip once; later runs reuse the file in data/raw/tiger/."""
    import requests

    zip_path = Path(zip_path)
    if not zip_path.exists():
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        zip_path.write_bytes(response.content)
    return zip_path


def load_bay_tracts(tract_source=None):
    """2020 tracts in the nine counties, in the project CRS."""
    import geopandas as gpd

    source = tract_source or f"zip://{download_tiger(TRACT_ZIP, f'{TIGER_BASE}/TRACT/tl_2020_06_tract.zip')}"
    tracts = gpd.read_file(source)
    tracts["county_fips"] = tracts["STATEFP"] + tracts["COUNTYFP"]
    tracts = tracts[tracts["county_fips"].isin(BAY_AREA_COUNTIES)]
    tracts = tracts.rename(columns={"GEOID": "tract_geoid"})[["tract_geoid", "county_fips", "ALAND", "AWATER", "geometry"]]
    return tracts.to_crs(PROJECT_CRS).reset_index(drop=True)


def load_places(place_source=None):
    """All 2020 California places (incorporated cities and CDPs), in the project CRS."""
    import geopandas as gpd

    source = place_source or f"zip://{download_tiger(PLACE_ZIP, f'{TIGER_BASE}/PLACE/tl_2020_06_place.zip')}"
    places = gpd.read_file(source)
    places["incorporated"] = places["CLASSFP"].str.startswith("C")
    places = places.rename(columns={"GEOID": "place_geoid", "NAME": "place_name"})
    return places[["place_geoid", "place_name", "incorporated", "geometry"]].to_crs(PROJECT_CRS)


def tract_to_place(tracts, places):
    """Spatial join: tract internal point within place polygon. One row per tract."""
    import geopandas as gpd

    points = gpd.GeoDataFrame(tracts[["tract_geoid", "county_fips"]],
                              geometry=tracts.geometry.representative_point(), crs=tracts.crs)
    joined = gpd.sjoin(points, places, how="left", predicate="within")
    if joined["tract_geoid"].duplicated().any():          # overlapping places: keep the first
        joined = joined.drop_duplicates("tract_geoid")
    joined["place_name"] = joined["place_name"].fillna("Unincorporated")
    joined["incorporated"] = joined["incorporated"].eq(True)
    return pd.DataFrame(joined[["tract_geoid", "county_fips", "place_geoid", "place_name", "incorporated"]])


def clean_tiger(tract_source=None, place_source=None):
    """Save Bay Area tract boundaries and the tract-to-place lookup. Returns both."""
    tracts = load_bay_tracts(tract_source)
    lookup = tract_to_place(tracts, load_places(place_source))
    Path(TIGER_TRACTS).parent.mkdir(parents=True, exist_ok=True)
    tracts.to_file(TIGER_TRACTS, layer="tracts", driver="GPKG")
    lookup.to_csv(TRACT_TO_PLACE, index=False)
    in_place = lookup["place_geoid"].notna()
    print(f"TIGER: {len(tracts)} tracts; {in_place.sum()} fall in a place "
          f"({lookup.loc[in_place, 'place_geoid'].nunique()} places), "
          f"{(~in_place).sum()} unincorporated")
    return tracts, lookup
