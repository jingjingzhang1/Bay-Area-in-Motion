"""Project paths and constants. All paths are relative to the project root.

To use data stored somewhere else (for example the shared Google Drive folder
in Colab), set the environment variable BAY_DATA_DIR before running:
    import os; os.environ["BAY_DATA_DIR"] = "/content/drive/My Drive/CP 101 Final Project Data Files"
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
