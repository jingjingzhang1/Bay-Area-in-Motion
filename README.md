# Bay Area in Motion: Mapping Daytime Population Changes, 2017–2023

CP 101 (UC Berkeley, Fall 2026) final project, Track B, MTC Mentor: Kaya Tollas

**Team "404: Static Not Found":** Hanzhen Yu, Jingjing Zhang, Happy Feng, Chiahao Ku

## Research question

How did commuter-driven daytime population shift across the nine-county San Francisco Bay Area between 2017 and 2023, and how do the patterns differ before (2017–2019), during (2020–2021) and after (2022–2023) the COVID-19 pandemic?

The nine counties are Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, Solano and Sonoma.

## Key measures

- **Net jobs** = WAC − RAC (jobs located in an area minus jobs held by people who live there)
- **Daytime population proxy (LODES)** = resident population + WAC − RAC
- **Daytime population proxy (ACS)** = resident population + workers by workplace − workers by residence
- **Commuting corridors**: home county → work county flows from the LODES origin-destination (OD) files

These are commuting-based proxies. They count primary jobs, not people physically present, and LODES does not capture remote work.

## Data sources

| Dataset | What we use | Years | Geography | Source |
|---|---|---|---|---|
| LEHD LODES v8 | OD main files, WAC and RAC (JT01 primary jobs, all workers), block crosswalk | 2017–2023 | 2020 blocks, summed to tract and county | https://lehd.ces.census.gov/data/lodes/LODES8/ca/ |
| ACS 1-year | B01003 population, B08301 workers by residence incl. work from home, B08604 workers by workplace, with 90% margins of error | 2017–2024 (no 2020 release) | County; places for coverage | Census API (downloaded by the code) |
| ACS 5-year | B01003 tract population (2019–2023 period) | 2023 release | Tract | https://data.census.gov/table/ACSDT5Y2023.B01003 |
| MTC Vital Signs | Tract population estimates (same values as ACS 5-year; used as a check) | 2017–2024 | Tract | https://vitalsigns.mtc.ca.gov |
| TIGER/Line 2020 | Counties, tracts, blocks, places; area water for the map water layer | 2020 vintage | — | https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html |

All Census sources are public-domain U.S. Government data.

## Repository structure

File names follow one pattern: `clean_*` cleans one dataset, analysis files are named for what they compute, `plot_*` makes charts. Output files start with the dataset or topic (`od_`, `validation_`, `daytime_`, `fig_`).

```
.
├── src/
│   ├── main.py                         # ONE entry point: clean -> analyze -> figures
│   ├── data/                           # loading and cleaning
│   │   ├── load_data.py                # readers for cleaned files (IDs kept as text)
│   │   ├── clean_od.py                 # LODES crosswalk + OD files, row log
│   │   ├── clean_wac_rac.py            # LODES WAC/RAC -> tract table
│   │   ├── clean_acs_county.py         # ACS 1-year county panel with MOEs (Census API)
│   │   ├── clean_acs_tract.py          # ACS 5-year tract population + MOE, Vital Signs check
│   │   ├── clean_acs_places.py         # optional: ACS 1-year city coverage
│   │   ├── clean_acs_blockgroups.py    # optional: ACS 5-year block-group coverage
│   │   ├── clean_tiger.py              # TIGER tracts/places + tract-to-city spatial join
│   │   ├── clean_water.py              # shared water layer for maps (TIGER area water)
│   │   ├── census_api.py               # shared Census API client (cache, retries, key from env)
│   │   └── convert_vital_signs.py      # optional: Vital Signs geodatabase -> shapefile (needs GDAL)
│   ├── analysis/
│   │   ├── od_corridors.py             # tract flows, county corridors, cross-county share
│   │   ├── validation.py               # OD vs WAC/RAC and OD vs ACS checks
│   │   └── daytime_population.py       # county, city and tract daytime proxies, WFH change, tract change
│   ├── visualization/
│   │   ├── plot_od.py                  # corridor trends, tract gain/loss
│   │   ├── plot_acs.py                 # WFH share, LODES vs ACS proxies, county daytime trend
│   │   ├── maps.py                     # add_water(ax): shared water layer on every map
│   │   └── plot_acs_coverage.py        # optional coverage charts
│   └── utils/
│       ├── config.py                   # all paths, file names, years, county codes
│       └── helpers.py                  # shared helpers (row counts, chart caption/save)
├── tests/test_acs_cleaning.py          # unit tests
├── docs/data_notes.md                  # cleaning decisions and data caveats
├── data/raw/  data/processed/          # data (not tracked in git)
├── outputs/tables/  outputs/figures/   # results written by src.main
├── notebooks/  reports/
├── requirements.txt  environment.yml
└── README.md
```

## Getting the data

Raw and processed data are included in `data/` (every file is under GitHub's 100 MB limit; files larger than 98 MB would go only in the submitted ZIP). Raw files keep their original Census names and are never edited; everything in `data/processed/` is rebuilt from `data/raw/` by `python -m src.main clean`.

| Folder | File(s) | Source |
|---|---|---|
| `data/raw/lodes/` | `ca_od_main_JT01_{2017..2023}.csv.gz`, `ca_xwalk.csv.gz` | LODES8 `ca/od/` and `ca/` |
| `data/raw/lodes/` | `ca_wac_S000_JT01_{2017..2023}.csv.gz`, `ca_rac_S000_JT01_{2017..2023}.csv.gz` | LODES8 `ca/wac/` and `ca/rac/` |
| `data/raw/acs/` | `ACSDT5Y2023.B01003.zip` | data.census.gov, table B01003, 2023 ACS 5-year, all California tracts |
| `data/raw/vital_signs/` | `vital_signs_tract_population_2017_2024.csv` | MTC Vital Signs, Population by tract |
| `data/processed/` | `tiger_tracts_bay_area_2020.gpkg`, `tiger_tract_to_place_2020.csv`, `lodes_od_bay_area_{year}.csv.gz`, `lodes_xwalk_bay_area.csv.gz`, `lodes_wac_rac_tracts_2017_2023.csv`, `acs1_county_2017_2024.csv`, `acs5_tract_population_2023.csv`, `tiger_water_bay_area_2020.gpkg` | written by `src.main clean` |

LODES files come from https://lehd.ces.census.gov/data/lodes/LODES8/ca/. The county ACS table is downloaded from the Census API by the code; setting `CENSUS_API_KEY` in your shell is optional. TIGER 2020 tracts and places are downloaded to `data/raw/tiger/` by `python -m src.main clean`; the water layer by `python -m src.main clean --extras`.

## How to run

Run every command from the project root folder.

```bash
git clone https://github.com/jingjingzhang1/Bay-Area-in-Motion.git
cd Bay-Area-in-Motion
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # or: conda env create -f environment.yml

python -m src.main                 # everything: clean -> analyze -> figures
```

Run one step at a time:

```bash
python -m src.main clean           # all data cleaning
python -m src.main analyze         # tables only
python -m src.main figures         # tables + charts
python -m src.main clean --extras  # also the map water layer and city / block-group ACS coverage
python -m src.main clean --force-refresh   # download Census API tables again
```

Steps whose output already exists are skipped, so re-running is safe. A missing input prints `MISSING ...` and the run continues with the rest. The first OD run takes several minutes because the raw files hold about 14 million rows per year.

**Google Colab with the shared Drive:**

```python
from google.colab import drive
drive.mount('/content/drive')
!git clone https://github.com/jingjingzhang1/Bay-Area-in-Motion.git
%cd Bay-Area-in-Motion
!pip install -q -r requirements.txt
import os
os.environ["BAY_DATA_DIR"] = "/content/drive/My Drive/<folder containing raw/ and processed/>"
!python -m src.main
```

**Tests:** `python -m unittest discover -s tests -v`

## Outputs

| File | Contents |
|---|---|
| `outputs/tables/od_row_log.csv`, `wac_rac_row_log.csv` | rows before and after cleaning, per year |
| `outputs/tables/od_top_county_corridors.csv` | 15 largest corridors by year, % change from 2017 and 2019 |
| `outputs/tables/od_top_tract_pairs_2023.csv`, `od_cross_county_share.csv` | largest tract flows; share of commutes crossing a county line |
| `outputs/tables/validation_od_vs_wac_rac.csv`, `validation_od_vs_acs.csv` | ballpark checks of the OD cleaning |
| `outputs/tables/daytime_county.csv` | county LODES and ACS daytime proxies, WFH share, by year |
| `outputs/tables/daytime_county_wfh_change.csv` | WFH share by county, 2017 vs 2023 |
| `outputs/tables/daytime_city.csv` | city (place) WAC, RAC, net jobs and daytime proxy by year, via the tract-to-city spatial join |
| `outputs/tables/daytime_tract.csv` | tract daytime proxy by year (fixed 2023 ACS 5-year population) |
| `outputs/tables/daytime_tract_net_change_2017_2023.csv` | change in net jobs per tract |
| `outputs/figures/fig_od_top_corridors_by_year.png` | top commuting corridors, 2017–2023 |
| `outputs/figures/fig_lodes_tract_gain_loss.png` | tracts with the largest gain and loss in net jobs |
| `outputs/figures/fig_acs_wfh_share_by_county.png` | work-from-home share by county |
| `outputs/figures/fig_acs_lodes_vs_acs_daytime.png` | LODES vs ACS county daytime proxies, 2023 |
| `outputs/figures/fig_acs_county_daytime_trend.png` | county daytime proxies over time, LODES-based vs ACS-only |

**Maps:** after `python -m src.main clean --extras`, call `add_water(ax, crs)` from `src.visualization.maps` after plotting the tracts, so the Bay, ocean and lakes show the same way on every map.

## Known limitations

- LODES counts primary jobs at the employer's reported address, so remote work is not reflected, and multi-site employers can concentrate jobs at one location.
- OD "main" files cover only workers who live and work in California; out-of-state commuters are excluded.
- There is no standard ACS 1-year release for 2020, and Napa's 2021–2022 resident-worker estimates are not published. These stay blank, never zero or interpolated.
- ACS 1-year covers only areas over 65,000 people, so year-by-year ACS comparisons are county-level. The tract proxy holds population fixed at the 2023 ACS 5-year estimate, so its changes reflect LODES job flows only.
- ACS values are survey estimates. County population (B01003) has no numeric margin of error because it is a controlled estimate; the published MOEs apply to counts, not to the proxies built from them.

More detail on each cleaning step is in [docs/data_notes.md](docs/data_notes.md).
