# Hanzhen's cleaning handoff

Run commands from the repository root after installing `requirements.txt`.
The original notebooks remain in the author's workspace; their embedded API key,
cell outputs, and local data files are excluded from this contribution.

| Original source | Reusable module | Responsibility |
| --- | --- | --- |
| `acs1yr.ipynb` | `src/data/acs_counties.py` | County ACS population, resident workers, WFH and workplace workers |
| `acs1yr_places.ipynb` | `src/data/acs_places.py` | Fixed 2023 place roster, 2017-2023 estimates, missingness and coverage exports |
| `acs5yr_blockgroups.ipynb` | `src/data/acs_blockgroups.py` | 2020-2024 estimates, MOEs, annotations and coverage exports |
| API calls shared by the notebooks | `src/data/census_api.py` | Retries, timeouts, response cache and environment-based credentials |
| `merge.ipynb` | `src/analysis/daytime_population.py` | County aggregation and daytime population comparisons |
| Notebook chart and HTML cells | `src/visualization/plot_acs_coverage.py` | Coverage tables/figures and county WFH chart |
| `convert_vital_signs.py` | `src/data/convert_vital_signs.py` | Numeric population fields and verified shapefile export |

`src/prepare_data.py` orchestrates these modules without changing the existing OD
workflow in `src/main.py` or teammates' cleaning code.

## Commands

Optionally set `CENSUS_API_KEY` in your shell. The Census client supports unkeyed
requests and never reads a key from another notebook. Public JSON responses are
cached under the processed data folder; `--force-refresh` refreshes them.

```bash
python -m src.prepare_data counties
python -m src.prepare_data places --plots
python -m src.prepare_data blockgroups --plots
python -m src.prepare_data merge --lodes data/processed/bay_area_wac_rac_2018_2023_cleaned.csv --plots
# Or run every stage with one command:
python -m src.prepare_data all --lodes data/processed/bay_area_wac_rac_2018_2023_cleaned.csv --plots
```

`BAY_DATA_DIR` continues to select a folder containing `raw/` and `processed/`.
`--processed-dir`, `--tables-dir`, and `--figures-dir` override destinations.
These commands regenerate their CSV/figure outputs; they reuse cached API responses.
Data and generated outputs remain untracked.

County exports go directly in `data/processed/`. Population uses
`bay_area_acs1_population_2017_2024.csv`. Worker exports use the existing long
filenames expected by `src.main`; the residence filename says 2018-2024 for
compatibility, but includes 2017 estimates from the source notebook. Workplace
estimates begin in 2018, matching the source. No 2017 workplace values are invented.
Place and block-group exports go in `acs1_jurisdiction_output/` and
`acs5_blockgroup_output/` beneath the processed folder. The merged table goes to
`outputs/tables/bay_area_daytime_population_merged.csv`; charts go to
`outputs/figures/` and coverage subfolders there.

For the optional Vital Signs export, install GDAL's `osgeo` Python bindings
in a compatible GIS environment (for example, `conda install -c conda-forge gdal`).
GDAL is imported only by the converter. Put the original geodatabase in `data/raw/`,
then run:

```bash
python -m src.data.convert_vital_signs
# Explicit input/output paths are also supported:
python -m src.data.convert_vital_signs --source /path/to/source.gdb --output-dir /path/to/new_export
```

The converter refuses an existing output directory. It exports a field-name
lookup and verifies feature count, geometry, CRS and every attribute.

## Interpretation and missingness

- GEOIDs/FIPS remain strings with leading zeros. Duplicate tract-years,
  duplicate county-years and inconsistent tract/county IDs stop the merge.
- Negative ACS sentinel codes become missing, with annotations and count MOEs
  retained in the block-group exports. Zero denominators yield missing WFH
  percentages. A request failure stops processing rather than becoming a missing estimate.
- Standard 2020 ACS 1-year values remain unavailable. The place panel explicitly
  keeps these gaps. The county merge now uses LODES as its left side, preserving
  2020 job totals while leaving population-based proxies and ACS fields blank.
- The place panel uses a fixed 2023 roster of incorporated places; it is not an
  annual boundary crosswalk. Unpublished small-place estimates remain missing.
- The block-group output is one ACS five-year release covering 2020-2024,
  not five annual observations. Derived WFH percentages have no calculated MOE.
- Both daytime population measures are proxies: population + WAC - RAC and
  population + workplace workers - resident workers. WFH is reported separately.
- The local WAC/RAC CSV is already cleaned. Its upstream cleaning code was not
  present, so the merge accepts it as an input and does not recreate that work.
  The local tract-check directory also contained outputs without source code.
  The available WAC/RAC input covers 2018-2023; this contribution does not supply
  the 2017 WAC/RAC file used by the separate OD workflow.

## Validation

```bash
python -m unittest discover -s tests -v
python -m compileall -q src
```

Local regression verification using cached public Census responses reproduced all
18 jurisdiction/block-group CSVs (707 jurisdiction-years, 101 incorporated places,
and 5,187 block groups), allowing only floating-point serialization differences.
The county merge reproduced all 45 original non-2020 county-years and retained
nine additional 2020 rows. Coverage figures/HTML rendered successfully. The Vital
Signs converter verified all 1,765 features, including geometry and attributes.
Live county API calls are covered with mocked responses in unit tests; a fresh
network download of county data was not required for these local checks.
