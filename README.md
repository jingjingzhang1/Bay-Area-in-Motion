# Bay Area in Motion: Mapping Daytime Population Changes, 2017–2023

CP 101 (UC Berkeley, Fall 2026) final project, Track B, MTC Mentor: Kaya Tollas

**Team "404: Static Not Found":** Hanzhen Yu, Jingjing Zhang, Happy Feng, Chiahao Ku

## Research question

How did commuter-driven daytime population shift across the nine-county San Francisco Bay Area between 2017 and 2023, and how do the patterns differ before (2017–2019), during (2020–2021) and after (2022–2023) the COVID-19 pandemic?

The nine counties are Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, Solano and Sonoma.

## Key measures

- **Net worker balance** = WAC − RAC (jobs located in an area minus jobs held by people who live there)
- **Daytime population proxy** = resident population + WAC − RAC
- **Commuting corridors**: home county → work county flows from the LODES origin-destination files

These are commuting-based proxies. They count primary jobs, not people physically present, and LODES does not capture remote work.

## Data sources

| Dataset | What we use | Years | Geography | Source |
|---|---|---|---|---|
| LEHD LODES v8 | WAC and RAC (S000, JT01 primary jobs); OD main files (JT01); `ca_xwalk` block crosswalk | 2017–2023 | 2020 census blocks, aggregated to tract and county | https://lehd.ces.census.gov/data/lodes/LODES8/ca/ |
| ACS 1-year | B01003 population, B08301 workers by residence (incl. work from home), B08604 workers by workplace | 2018–2024 (no 2020 release) | County | https://data.census.gov |
| TIGER/Line 2020 | Counties, tracts, blocks, places | 2020 vintage | — | https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html |

All sources are public-domain U.S. Census Bureau data.

## Repository structure

```
.
├── src/
│   ├── main.py                  # runs the full analysis
│   ├── data/
│   │   ├── load_data.py         # read raw and processed files (IDs kept as text)
│   │   └── process_data.py      # clean the crosswalk and OD files
│   ├── analysis/
│   │   └── compute_metrics.py   # row logs, commuting flows, corridors, validation, tract change
│   ├── visualization/
│   │   └── plot_results.py      # report charts (title, labels, units, caption)
│   └── utils/
│       ├── config.py            # paths, years, county codes
│       └── helpers.py           # small shared helpers
├── notebooks/                   # exploration and prototyping notebooks
├── data/
│   ├── raw/                     # original downloads (not tracked in git)
│   └── processed/               # cleaned files (not tracked in git)
├── outputs/
│   ├── tables/
│   └── figures/
├── images/                      # reference images and diagrams
├── reports/                     # midterm and final report PDFs
├── requirements.txt
├── environment.yml
└── README.md
```

## Getting the data

Data files are not stored in this repository because they are too large. Download them yourself or copy them from the team's shared Google Drive folder.

Put these in `data/raw/`, from https://lehd.ces.census.gov/data/lodes/LODES8/ca/:
- `ca_od_main_JT01_{year}.csv.gz` for 2017–2023 (from the `od/` folder)
- `ca_xwalk.csv.gz`

Put these in `data/processed/`, from the shared Drive:
- `bay_area_wac_rac_2017_2023_cleaned.csv` (cleaned WAC/RAC by tract)
- `bay_area_acs1_B08301_workers_by_where_they_live_and_working_from_home_2018_2024.csv`
- `bay_area_acs1_B08604_workers_by_workplace_2018_2024.csv`

## How to run

### Locally

```bash
git clone <repo-url>
cd bay-area-in-motion
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt  # or: conda env create -f environment.yml
python -m src.main
```

Run the command from the project root folder. Tables are written to `outputs/tables/` and figures to `outputs/figures/`. Steps whose output already exists are skipped, so re-running is safe.

### In Google Colab, using the shared Drive

```python
from google.colab import drive
drive.mount('/content/drive')

!git clone <repo-url>
%cd bay-area-in-motion
!pip install -r requirements.txt

import os
os.environ["BAY_DATA_DIR"] = "/content/drive/My Drive/<path to a folder containing raw/ and processed/>"
!python -m src.main
```

`BAY_DATA_DIR` points the code at a data folder outside the repo. If it is not set, the code uses `data/` inside the repo.

## Outputs

- `outputs/tables/`: OD row-count log, tract-to-tract flows, top commuting corridors by year, validation tables (OD vs WAC/RAC, OD vs ACS)
- `outputs/figures/`: top commuting corridors by year, top-10 tract gain/loss in net jobs

## Known limitations

- LODES counts primary jobs at the employer's reported address, so remote work is not reflected, and multi-site employers can concentrate jobs at one location.
- OD "main" files cover only workers who live and work in California; out-of-state commuters are excluded.
- ACS 1-year data is not published for 2020 or for areas under 65,000 people, so ACS comparisons are county-level only.
- ACS values are survey estimates with margins of error.
