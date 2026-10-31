"""Small helpers shared across the project."""
import matplotlib.pyplot as plt
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


def set_chart_style():
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def add_caption(fig, text):
    """One-sentence caption under a figure (every report chart has one)."""
    fig.text(0.01, -0.02, text, ha="left", va="top", fontsize=8.5, wrap=True)


def save_figure(fig, name):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / name, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return FIGURES_DIR / name
