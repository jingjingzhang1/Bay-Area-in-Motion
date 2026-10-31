"""Shared Census client: cache public responses and keep credentials out of files."""
import hashlib
import json
import os
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.utils.config import BAY_AREA_COUNTIES

COUNTIES = {code[2:]: name for code, name in BAY_AREA_COUNTIES.items()}
STATE = "06"
VARIABLES = {
    "B01003_001E": "population",
    "B08301_001E": "workers_residence",
    "B08301_021E": "work_from_home",
    "B08604_001E": "workers_workplace",
}
METRICS = list(VARIABLES.values())


class CensusClient:
    def __init__(self, cache_dir, force_refresh=False):
        self.cache_dir = Path(cache_dir)
        self.force_refresh = force_refresh
        self.api_key = os.environ.get("CENSUS_API_KEY", "").strip()
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=Retry(
            total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
        )))

    def table(self, year, dataset, params):
        url = f"https://api.census.gov/data/{year}/{dataset}"
        signature = json.dumps([url, params], sort_keys=True)
        cache = self.cache_dir / (hashlib.sha256(signature.encode()).hexdigest() + ".json")
        if cache.exists() and not self.force_refresh:
            data = json.loads(cache.read_text(encoding="utf-8"))
        else:
            query = dict(params)
            if self.api_key:
                query["key"] = self.api_key
            try:
                response = self.session.get(url, params=query, timeout=(15, 120))
            except requests.RequestException:
                raise RuntimeError(f"Census request failed: {year}/{dataset}, {params['for']}") from None
            if response.status_code != 200:
                raise RuntimeError(
                    f"Census HTTP {response.status_code}: {year}/{dataset}, {params['for']}. "
                    "A request failure is not a missing estimate."
                )
            try:
                data = response.json()
            except ValueError:
                raise RuntimeError(f"Non-JSON Census response: {year}/{dataset}") from None
        if (not isinstance(data, list) or len(data) < 2
                or not isinstance(data[0], list)
                or any(not isinstance(row, list) or len(row) != len(data[0]) for row in data)):
            raise ValueError(f"Invalid Census table: {year}/{dataset}")
        if not cache.exists() or self.force_refresh:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(data), encoding="utf-8")
        return pd.DataFrame(data[1:], columns=data[0])


def clean_counts(frame, columns):
    """Mask negative ACS sentinel codes; retain zero and missing values."""
    for column in columns:
        numeric = pd.to_numeric(frame[column], errors="coerce")
        frame[column] = numeric.mask(numeric < 0)
    return frame


def add_coverage(frame):
    frame["work_from_home_pct"] = (
        100 * frame["work_from_home"]
        / frame["workers_residence"].where(frame["workers_residence"] > 0)
    )
    frame["missing_metrics"] = frame[METRICS].apply(
        lambda row: "; ".join(row.index[row.isna()]), axis=1
    )
    return frame
