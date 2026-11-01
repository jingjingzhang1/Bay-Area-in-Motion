"""Shared water layer for all maps (Happy Feng).

Downloads TIGER/Line 2020 area-water polygons for the nine Bay Area counties, combines
them into one layer in the project CRS and saves it, so every map draws the same water
on top of the tract data.

TIGER area water already includes San Francisco Bay, San Pablo Bay and the Pacific Ocean
(MTFCC H2051/H2053), so no separate MTC Bay layer is needed. Each TIGER file is published
per county and cut at the county line, so the combined layer is already limited to the
nine counties.
"""
from pathlib import Path

import pandas as pd

from src.utils.config import BAY_AREA_COUNTIES, RAW_DIR, WATER_LAYER, PROJECT_CRS

TIGER_URL = "https://www2.census.gov/geo/tiger/TIGER2020/AREAWATER/tl_2020_{fips}_areawater.zip"


def download_county_water(fips, raw_dir=RAW_DIR / "tiger_water"):
    """Download (once) and read one county's TIGER area-water shapefile."""
    import geopandas as gpd
    import requests

    raw_dir = Path(raw_dir)
    zip_path = raw_dir / f"tl_2020_{fips}_areawater.zip"
    if not zip_path.exists():
        raw_dir.mkdir(parents=True, exist_ok=True)
        response = requests.get(TIGER_URL.format(fips=fips), timeout=120)
        response.raise_for_status()
        zip_path.write_bytes(response.content)
    return gpd.read_file(f"zip://{zip_path}")


def clean_water(output_path=WATER_LAYER, crs=PROJECT_CRS):
    """Combine the nine counties' water polygons into one GeoPackage in the project CRS."""
    import geopandas as gpd

    frames = []
    for fips in BAY_AREA_COUNTIES:
        county = download_county_water(fips)
        county["county_fips"] = fips
        frames.append(county)
        print(f"Water {BAY_AREA_COUNTIES[fips]}: {len(county)} polygons")
    water = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=frames[0].crs).to_crs(crs)
    water = water[["county_fips", "FULLNAME", "MTFCC", "AWATER", "geometry"]]
    water["geometry"] = water.geometry.make_valid()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    water.to_file(output_path, layer="water", driver="GPKG")
    print(f"Water layer: {len(water)} polygons in {crs} saved to {Path(output_path).name}")
    return water
