# Hanzhen's data contribution

This contribution copies Hanzhen Yu's project data from the local CYPLAN 101
workspace into the current shared repository. Original filenames and bytes are
preserved. The source notebooks and local credential settings are not included.
Hanzhen's cleaning code is already present in the repository's current modules.
The abandoned shared repository was also inspected; it contained no additional
tracked data files to migrate.

## Where the files are

| Location | Contents |
| --- | --- |
| `data/raw/vital_signs/` | Original Vital Signs CSV, GeoJSON, ZIP, geodatabase, and original `geo_export_*` shapefile with its companion files |
| `data/raw/census_api_cache/` | Public Census JSON responses from the place and block-group notebooks; original cache subfolders and filenames retained |
| `data/processed/` | Original county ACS exports, cleaned 2018–2023 WAC/RAC, and original daytime population merge |
| `data/processed/acs1_jurisdiction_output/` | Place estimates, roster, coverage tables, and figures |
| `data/processed/acs5_blockgroup_output/` | Block-group estimates, MOEs, annotations, coverage tables, and figure |
| `data/processed/acs5_tract_check_output/` | Tract workplace estimates and coverage check |
| `data/processed/vital_signs_shapefile/` | Converted shapefile with all companion files and field-name lookup |
| `data/processed/hanzhen_cleaning/` | County exports from the prior cleaning checkout that differ from the original local exports |
| `outputs/hanzhen_cleaning/` | Prior cleaning replay's merged table, coverage figures/HTML, and WFH chart |
| `outputs/figures/Covid_pop_change.png` | Existing population-change figure |
| `reports/Covid_pop_change.pdf` | Existing population-change report |

[The inventory](hanzhen_data_inventory.csv) lists all 221 contributed files,
their original workspace locations, repository paths, byte counts, and SHA-256
checksums. The total uncompressed size is approximately 133.64 MiB; the largest
individual file is 27.28 MiB. Every copied file was checked against its source.

## Filenames and interpretation

Run project code from the repository root. The original CSV names are retained;
do not substitute the 2018–2023 WAC/RAC file for the separate 2017–2023 input
without checking year coverage. The original merged table and the replayed
cleaning result are both retained: the replay keeps 2020 LODES rows with missing
ACS fields, whereas the original merge omitted those rows.

The latest pipeline generates consolidated county and tract outputs under names
configured in `src/utils/config.py`. These source exports are not renamed or
presented as those newer outputs. In particular, the original Vital Signs CSV is
`data/raw/vital_signs/Vital_Signs__Population_-_Tracts_20261028.csv`; it is not
silently renamed to the newer pipeline's default CSV input name. The original
geodatabase and converted shapefile already use their configured directory names.

Place estimates cover 2017–2023 and have missing unpublished ACS observations,
including the standard 2020 ACS 1-year gap. Block-group estimates are one ACS
five-year release covering 2020–2024. Keep geographic IDs as text when reading
these CSVs so leading zeros survive. See [the data notes](data_notes.md) for
cleaning decisions and caveats.

The local clone uses sparse checkout to omit teammates' large LODES datasets
while retaining their files in Git history and on GitHub. This data contribution
does not delete or overwrite their tracked files. To download the entire shared
repository later, run `git sparse-checkout disable` (this downloads the omitted
large datasets).
