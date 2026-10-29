"""Small helpers shared across the project."""
import pandas as pd

from src.utils.config import TABLES_DIR, FIGURES_DIR


def make_output_dirs():
    """Create the output folders if they do not exist yet."""
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def count_rows(path):
    """Count rows in a (possibly gzipped) CSV without loading it all into memory."""
    return sum(len(c) for c in pd.read_csv(path, usecols=[0], chunksize=1_000_000))


def tract_number(geoid):
    """Turn an 11-digit tract GEOID into its tract number, e.g. 06075012405 -> '124.05'."""
    code = geoid[-6:]
    base, suffix = str(int(code[:4])), code[4:]
    return base if suffix == "00" else f"{base}.{suffix}"
