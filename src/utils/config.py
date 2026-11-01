"""Project paths, file names and constants. Every path is relative to the project root.

To read data stored somewhere else (for example the shared Google Drive folder in
Colab), set the environment variable BAY_DATA_DIR to a folder that contains
raw/ and processed/ before running:
    import os; os.environ["BAY_DATA_DIR"] = "/content/drive/My Drive/<data folder>"
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("BAY_DATA_DIR", PROJECT_ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

OUTPUT_DIR = PROJECT_ROOT / "outputs"
TABLES_DIR = OUTPUT_DIR / "tables"
FIGURES_DIR = OUTPUT_DIR / "figures"

YEARS = list(range(2017, 2024))
PROJECT_CRS = "EPSG:26910"   # NAD83 / UTM zone 10N, meters; used for every map and area calculation
PRE_COVID_YEAR = 2019
CHUNK_ROWS = 1_000_000

BAY_AREA_COUNTIES = {
    "06001": "Alameda",
    "06013": "Contra Costa",
    "06041": "Marin",
    "06055": "Napa",
    "06075": "San Francisco",
    "06081": "San Mateo",
    "06085": "Santa Clara",
    "06095": "Solano",
    "06097": "Sonoma",
}

# ---- Raw inputs (data/raw/) ----
RAW_XWALK = RAW_DIR / "lodes" / "ca_xwalk.csv.gz"
RAW_OD_PATTERN = "ca_od_main_JT01_{year}.csv.gz"          # in data/raw/lodes/
RAW_ACS5_TRACT_ZIP = RAW_DIR / "acs" / "ACSDT5Y2023.B01003.zip"
RAW_VITAL_SIGNS_TRACTS = RAW_DIR / "vital_signs" / "vital_signs_tract_population_2017_2024.csv"
RAW_VITAL_SIGNS_GDB = RAW_DIR / "vital_signs" / "Vital_signs_tracts_pop_estimate.gdb"

# ---- Cleaned data (data/processed/) ----
XWALK_BAY = PROCESSED_DIR / "lodes_xwalk_bay_area.csv.gz"
OD_PATTERN = "lodes_od_bay_area_{year}.csv.gz"
WAC_RAC_TRACTS = PROCESSED_DIR / "lodes_wac_rac_tracts_2017_2023.csv"
ACS_COUNTY = PROCESSED_DIR / "acs1_county_2017_2024.csv"
ACS_TRACT_POPULATION = PROCESSED_DIR / "acs5_tract_population_2023.csv"
ACS_PLACES_DIR = PROCESSED_DIR / "acs1_places"
ACS_BLOCKGROUPS_DIR = PROCESSED_DIR / "acs5_blockgroups"
CENSUS_CACHE_DIR = PROCESSED_DIR / "census_api_cache"
VITAL_SIGNS_SHAPEFILE_DIR = PROCESSED_DIR / "vital_signs_shapefile"
WATER_LAYER = PROCESSED_DIR / "tiger_water_bay_area_2020.gpkg"
TIGER_TRACTS = PROCESSED_DIR / "tiger_tracts_bay_area_2020.gpkg"
TRACT_TO_PLACE = PROCESSED_DIR / "tiger_tract_to_place_2020.csv"


def raw_od_path(year):
    return RAW_DIR / "lodes" / RAW_OD_PATTERN.format(year=year)


def od_path(year):
    return PROCESSED_DIR / OD_PATTERN.format(year=year)
