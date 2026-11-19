# Missing Data and Dark Data: Bay Area in Motion

## Overview

This document explains five missing-data and data-quality issues in our Bay Area analysis. We identify the number of affected records, the type and cause of dark data, possible bias, and our decision to drop, flag, or leave values blank.

The counts below refer to different datasets and geographic units. They should not be added together.

## 1. Missing 2020 ACS 1-Year Data

**Affected records:** 9 county-year records (one for each Bay Area county in 2020).

**Dark-data type and reason:** Data unavailable because of a disruption in official data publication. The Census Bureau did not release the standard 2020 ACS 1-year estimates.

**Possible bias:** Without 2020 observations, we cannot directly measure county-level changes during the first year of COVID-19 using this ACS series. Comparing 2019 with 2021 may hide short-term changes and make the pandemic transition appear smoother than it actually was.

**Handling decision:** We leave 2020 ACS 1-year observations missing rather than interpolate them or substitute another dataset. We do not interpret missing values as zero.

## 2. Missing Napa County Data, 2021–2022

**Affected records:** 2 county-year records, one in 2021 and one in 2022, in the ACS B08301 dataset.

**Dark-data type and reason:** Unavailable or unpublished estimates. Napa County's B08301 values are not published for these two years. Census missing-value codes were converted to missing values during data cleaning.

**Possible bias:** Excluding Napa from regional calculations reduces geographic coverage. If Napa's commuting and work-from-home patterns differed from those of the other counties, regional estimates based only on available counties may be biased. The direction cannot be established from the missing observations.

**Handling decision:** We retain the Napa county-year records but leave the affected commuting and work-from-home fields blank (`NaN`). We do not replace them with zero or invent estimates.

## 3. Seven Water Census Tracts

**Affected records:** 7 water tracts identified in the geographic validation data. The broader geographic reference contains 1,772 tracts, including 1,765 land tracts.

**Dark-data type and reason:** Geographic non-applicability rather than ordinary missing survey responses. These water tracts have zero resident population and are not appropriate units for residential population-based analysis.

**Possible bias:** Including zero-population water tracts in tract-level summaries may distort geographic coverage and produce undefined per-resident ratios. Removing them means our tract-level results describe land tracts rather than every tract polygon.

**Handling decision:** We exclude these seven water tracts from land-based population analyses and keep their identification documented in `data/processed/acs_validation/acs_only_7_water_tracts.csv`. They should not be confused with other zero-population records reported by separate validation checks.

## 4. Census Tracts With Fewer Than 500 Residents

**Affected records:** 11 tracts reported in `tract_validation.json`.

**Dark-data type and reason:** Low-population and small-denominator data limitations. These tracts have population estimates below 500, making per-resident indicators potentially unstable.

**Possible bias:** Small changes in the numerator or denominator can produce large changes in per-resident ratios. If these tracts are excluded from an analysis, results may underrepresent sparsely populated areas.

**Handling decision:** We flag tracts with fewer than 500 residents and leave their per-resident ratios blank. We do not automatically remove them from every dataset or treat their population as zero.

## 5. Large Margins of Error (MOE)

**Affected records:** 3 tracts with resident-population relative MOE greater than 50%, as reported in `tract_validation.json`.

**Dark-data type and reason:** Statistical uncertainty in survey-based estimates. The ACS population estimates have large margins of error relative to their estimated values.

**Possible bias:** These estimates may be too imprecise for reliable tract-level comparisons. Treating them as exact values could exaggerate spatial differences or apparent changes.

**Handling decision:** We flag population estimates with relative MOE above 50%. These observations require caution in interpretation and should not be presented as equally precise as estimates with smaller MOEs. The available MOE describes resident-population uncertainty, not uncertainty for the complete daytime-population proxy or LODES employment counts.

## Limitations and Interpretation

These five issues do not all represent the same kind of missingness. Some observations were never published, some geographic units are not applicable to residential analysis, and others are available but statistically unreliable.

Our approach is to preserve valid observations, identify limitations explicitly, and avoid treating missing values as zeros. We do not use interpolation to create unavailable ACS observations. We also avoid claiming that missingness has a known positive or negative effect when the available evidence cannot establish its direction.

The validation report separately identifies four zero-resident-population tracts. This count should not be added to the seven water tracts without checking whether the geographic populations and datasets overlap.

## Data Sources and Validation

- `docs/data_notes.md` — cleaning decisions and data limitations.
- `data/processed/acs_cleaning/` — cleaned ACS county-level data.
- `data/processed/acs_validation/tract_validation.json` — tract population and MOE validation.
- `data/processed/acs_validation/acs_only_7_water_tracts.csv` — seven water tracts.
- `src/data/clean_acs_county.py` — ACS county cleaning.
- `src/data/clean_acs_tract.py` — ACS tract population cleaning.

**Scope note:** The 11 low-population tracts and 3 high-relative-MOE tracts are validation counts for the resident-population dataset. They should not be interpreted as counts of all missing or unreliable observations across every year and variable in the project.