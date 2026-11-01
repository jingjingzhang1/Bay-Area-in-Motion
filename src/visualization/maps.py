"""Map helpers shared by every map in the project."""
from src.utils.config import WATER_LAYER


def add_water(ax, target_crs="EPSG:4269", water_path=WATER_LAYER):
    """Draw the shared Bay Area water layer on ax, above the tract data (Happy Feng).

    Pass the CRS of the map being drawn, e.g. add_water(ax, tracts.crs).
    Build the layer first with `python -m src.main clean --extras`.
    """
    import geopandas as gpd

    water = gpd.read_file(water_path).to_crs(target_crs)
    water.plot(ax=ax, color="lightblue", edgecolor="none", zorder=3)
    return ax
