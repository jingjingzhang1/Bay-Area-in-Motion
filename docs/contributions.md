# Contributions

Who did what for the midterm checkpoint (through November 2, 2026). File paths point to the code or data each person wrote or prepared. GitHub's contributor count is based on number of commits, so it does not reflect the amount of work: uploading files one at a time through the GitHub website creates one commit per file.

## Jingjing Zhang
- Downloaded and cleaned the LODES origin-destination data for 2017–2023 and the block crosswalk, with a row-count log (`src/data/clean_od.py`)
- Commuting corridor analysis and validation of the OD data against WAC/RAC and ACS (`src/analysis/od_corridors.py`, `src/analysis/validation.py`)
- Set up the GitHub repository: folder structure, README and `requirements.txt`
- Consolidated all members' code into one structure and a single pipeline entry point (`src/main.py`): unified file names, removed duplicate county ACS code, and wrote the WAC/RAC cleaning and tract ACS functions in their current form (`src/data/clean_wac_rac.py`, `src/data/clean_acs_tract.py`)
- Tract-to-city spatial join and city-level daytime table (`src/data/clean_tiger.py`, `city_daytime` in `src/analysis/daytime_population.py`)
- Reprojected the shared water layer to the project CRS; organized data into `data/raw/` and `data/processed/`; removed duplicate uploads
- Uploaded the OD raw and processed data; ran the full pipeline end to end and committed the output tables and figures
- Reviewed and merged 8 of the 10 pull requests
- Revised the proposal after mentor feedback and planned and assigned team tasks
- Report: Data section

## Hanzhen Yu
- ACS 1-year county, place and block-group cleaning and the shared Census API client (`src/data/clean_acs_county.py`, `clean_acs_places.py`, `clean_acs_blockgroups.py`, `census_api.py`), with tests
- MTC Vital Signs data and converter (`src/data/convert_vital_signs.py`); county daytime population merge
- Uploaded ACS and Vital Signs raw and processed data; county ACS snapshot so the pipeline runs without a Census API key
- Population change map, drawn in ArcGIS Pro from the project's processed data (made outside the code pipeline; included in the submission ZIP)
- Report: Methods; assembled the midterm report

## Chiahao Ku
- TIGER/Line 2020 boundaries and block-to-place assignment; 2019–2023 tract, city and county maps
- ACS 2017 county tables with margins of error and the ACS 5-year tract population (original scripts later consolidated into `src/data/clean_acs_county.py` and `clean_acs_tract.py`)
- Work-from-home and LODES vs ACS daytime population charts (`src/visualization/plot_acs.py`)
- Uploaded ACS raw and processed data; merged 2 pull requests
- Tested the full pipeline (`python -m src.main`) and helped get it running end to end
- Report: Early Results

## Happy Feng
- Cleaned LODES WAC/RAC for 2017–2023 and checked tract IDs against TIGER 2020 (method in `src/data/clean_wac_rac.py`); uploaded the WAC/RAC raw data and cleaned tract table
- Built the shared map water layer and `add_water()` helper (`src/data/clean_water.py`, `src/visualization/maps.py`)
- County daytime population trend chart, LODES-based vs ACS-only (`plot_county_daytime_trend` in `src/visualization/plot_acs.py`)
- Report: Research Question and Plan to Finish
