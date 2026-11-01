"""Map helpers shared by every map in the project."""
from functools import lru_cache

from src.utils.config import WATER_LAYER, PROJECT_CRS


@lru_cache(maxsize=1)
def load_water(water_path=WATER_LAYER):
    """Read the shared water layer once per run."""
    import geopandas as gpd
    return gpd.read_file(water_path)


def add_water(ax, target_crs=PROJECT_CRS, water_path=WATER_LAYER):
    """Draw the shared Bay Area water layer on ax, above the tract data (Happy Feng).

    The layer is stored in the project CRS (EPSG:26910); reproject the tracts to it
    first, or pass the map's CRS, e.g. add_water(ax, tracts.crs).
    Build the layer with `python -m src.main clean --extras`.
    """
    water = load_water(water_path)
    if water.crs != target_crs:
        water = water.to_crs(target_crs)
    water.plot(ax=ax, color="lightblue", edgecolor="none", zorder=3)
    return ax
