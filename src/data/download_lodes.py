"""Download the raw LODES origin-destination (OD) files that are too large for GitHub.

Each file is 80-90 MB, over the 50 MB limit for committed files, so it is not in the
repository. The processed OD files in data/processed/ are committed, so most people never
need these downloads; they are only needed to re-run the OD cleaning from scratch.

Usage (from the project root):
    python -m src.data.download_lodes              # all years, 2017-2023
    python -m src.data.download_lodes 2019 2023    # only some years

Files that already exist and pass a gzip check are skipped.
"""
import gzip
import shutil
import sys
import urllib.request
from pathlib import Path

from src.utils.config import RAW_DIR, RAW_OD_PATTERN, YEARS

BASE_URL = "https://lehd.ces.census.gov/data/lodes/LODES8/ca/od/"
USER_AGENT = "bay-area-in-motion-student-project"


def is_valid_gzip(path):
    """True if the file exists and decompresses to the end without error."""
    try:
        with gzip.open(path, "rb") as f:
            while f.read(1 << 20):
                pass
        return True
    except (OSError, EOFError):
        return False


def download_od_year(year):
    """Download one year of OD main (JT01) data into data/raw/lodes/. Returns True on success."""
    name = RAW_OD_PATTERN.format(year=year)
    target = RAW_DIR / "lodes" / name
    if target.exists() and is_valid_gzip(target):
        print(f"Skipping {name} (already downloaded)")
        return True
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(name + ".part")
    url = BASE_URL + name
    print(f"Downloading {url}")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=60) as response, open(partial, "wb") as out:
            shutil.copyfileobj(response, out, length=1 << 20)
    except OSError as error:
        print(f"FAILED {name}: {error}")
        partial.unlink(missing_ok=True)
        return False
    if not is_valid_gzip(partial):
        print(f"FAILED {name}: downloaded file is not a complete gzip file")
        partial.unlink(missing_ok=True)
        return False
    partial.replace(target)
    print(f"Saved {target} ({target.stat().st_size / 1e6:.0f} MB)")
    return True


def main(argv):
    years = [int(a) for a in argv] or YEARS
    results = [download_od_year(year) for year in years]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
