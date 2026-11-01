# Data notes: cleaning decisions and caveats

Each section lists what the step does, why, and what to report. Code locations are in brackets.

## LODES crosswalk and OD [`src/data/clean_od.py`]

- The crosswalk keeps the blocks in the nine Bay Area counties.
- OD uses only the **main** files (people who live and work in California) and only primary jobs (JT01), so each worker is counted once. The **aux** files (workers living out of state) are left out because the project is about commuting within California.
- A row is kept if the home block **or** the work block is in the Bay Area. Rows with a missing block ID and exact duplicates are dropped.
- County and tract IDs are the first 5 and 11 digits of the 2020 block ID. LODES v8 uses 2020 blocks, which nest inside 2020 tracts and counties. All Bay Area block IDs in the 2019 and 2023 LODES files matched TIGER 2020 blocks.
- Row counts for every year are written to `outputs/tables/od_row_log.csv`.

## LODES WAC/RAC [`src/data/clean_wac_rac.py`] (Happy)

- Uses the all-jobs total (C000) for primary jobs (JT01), summed from blocks to 2020 tracts. WAC is summed by work block and RAC by home block.
- A tract with jobs on only one side gets 0 on the other side, since it has no jobs or no resident workers recorded.
- Example (2017): 252,128 statewide WAC blocks -> 49,244 in the Bay Area (80.5% dropped); 363,224 RAC blocks -> 62,832 (82.7% dropped).
- Output: `tract_geoid, WAC, RAC, net_change, year, county_fips`, 1,765 tracts × 7 years = 12,355 rows, no duplicates or negative counts. All 1,765 tracts match TIGER 2020 tract GEOIDs (100%); the other 7 of the 1,772 TIGER tracts are water tracts with zero population.

## ACS county [`src/data/clean_acs_county.py`]

- Census API, ACS 1-year, tables B01003, B08301 (`_001` total and `_021` worked from home) and B08604, with 90% MOEs, for 2017–2024.
- **2020 is not requested:** there is no standard ACS 1-year release for 2020.
- Negative Census sentinel codes become missing, never zero. This affects Napa B08301 in 2021–2022, which is not published, and every B01003 MOE, because population is a controlled estimate with no numeric MOE.
- A failed request stops the run instead of becoming a missing estimate. Responses are cached under `data/processed/census_api_cache/`.
- The MOEs are for the published counts only. They are not MOEs for ratios such as the WFH share, or for the daytime proxies.

## ACS tract population [`src/data/clean_acs_tract.py`]

- 2023 ACS 5-year B01003, covering 2019–2023, for 1,772 Bay Area tracts, with 90% MOE.
- Flags: population under 500, and relative MOE over 50%. Per-resident ratios are left blank for tracts under 500 people.
- MTC Vital Signs tract population for 2023 equals these ACS 5-year estimates for all 1,765 land tracts. The Vital Signs file is used only as a check.
- Vital Signs earlier years are also ACS 5-year estimates, so neighbouring years overlap by four years. They are not independent annual values.

## Daytime proxies [`src/analysis/daytime_population.py`]

- **County:** LODES proxy = population + WAC − RAC, and ACS proxy = population + workers by workplace − workers by residence. All WAC/RAC years are kept; ACS fields stay blank for 2020.
- **Tract:** the population is fixed at the 2023 ACS 5-year estimate for every year, so changes over time reflect LODES net job flows only, not changes in resident population.
- Both are commuting-based proxies, not counts of people physically present.

## Validation [`src/analysis/validation.py`]

- OD totals by county compared with WAC and RAC: expect ratios slightly under 1, because OD main excludes out-of-state residents.
- OD totals compared with ACS workers: expect about 0.8–1.0, because LODES excludes self-employed workers. The county rank correlation should be close to 1.

## Optional coverage work [`clean_acs_places.py`, `clean_acs_blockgroups.py`, `plot_acs_coverage.py`]

- Places: a fixed 2023 roster of incorporated places with ACS 1-year 2017–2023 estimates. Places too small for ACS 1-year stay missing. This is not an annual boundary crosswalk.
- Block groups: one ACS 5-year release (2020–2024) with MOEs and annotations. It is a single release, not five annual observations.
- `convert_vital_signs.py` needs GDAL (`conda install -c conda-forge gdal`) and refuses to overwrite an existing output folder.

## Map water layer [`src/data/clean_water.py`, `src/visualization/maps.py`] (Happy)

- TIGER/Line 2020 area-water polygons for the nine counties (3,518 polygons), combined into one GeoPackage and reprojected to the project CRS, EPSG:26910 (NAD83 / UTM 10N, meters). It already includes San Francisco Bay, San Pablo Bay and the Pacific Ocean, so no separate MTC Bay layer is needed, and each TIGER file is cut at its county line, so no extra clipping is needed.
- `add_water(ax, crs)` draws it above the tract data on every map, so all maps show water the same way (mentor Kaya's suggestion).
