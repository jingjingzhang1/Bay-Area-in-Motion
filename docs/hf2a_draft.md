# HF2a — Earnings-band employment balance draft

## Scope and method
Nine Bay Area counties, 1,765 tracts, annual LODES JT01 primary jobs, 2017–2023. Input: `data/processed/lodes_wac_rac_tracts_2017_2023.csv` from repository revision `07f444e8bd2dce18135ceb9b3cb6645e3d711439`. This task checks the processed panel, not the raw-file cleaning lineage.

CE01: <= $1,250/month; CE02: $1,251–$3,333/month; CE03: > $3,333/month. These are nominal job earnings bands, not household incomes or inflation-adjusted worker classes. Workers can move between bands over time.

For each tract, band and year: net_jobs = WAC_band − RAC_band. Positive means more primary jobs located in the tract than primary-job workers residing there; negative means the reverse. County values sum tract counts, not ratios. Internal flows cancel in the balance. This is not an OD route analysis or a count of people physically present.

Periods: pre = 2017–2019 (3 years), during = 2020–2021 (2), post = 2022–2023 (2). Period tables use arithmetic means of annual counts. Changes subtract these means (post − pre, during − pre, post − during), in jobs. An alternative is period sums; we avoid them because the periods have unequal lengths. An alternative is 2019 vs 2023 endpoints; means reduce dependence on individual years but may hide within-period variation. We avoid percentage change of signed balances because zero crossings and small denominators make it misleading.

## Outputs
- `hf2a_tract_annual.csv`: 37,065 tract-year-band rows.
- `hf2a_county_annual.csv`: 189 county-year-band rows.
- `hf2a_tract_period_means.csv`: 15,885 tract-period-band rows.
- `hf2a_county_period_means.csv`: 81 county-period-band rows.
- `hf2a_tract_period_changes.csv`: 5,295 tract-band rows.
- `hf2a_county_period_changes.csv`: 27 county-band rows.

Keep GEOIDs as text when importing CSVs into spreadsheet applications. Negative values are valid balances. Decimal period averages are expected even though annual job counts are integers.

## Draft observations (post-period mean minus pre-period mean)
1. San Francisco: high-band net jobs increased by 50,714.3 (198,643.7 to 249,358.0), while low-band net jobs fell by 3,741.8 (18,187.3 to 14,445.5). Meaning: employer-location balances evolved differently by earnings band. Caveat: employer job locations do not establish physical attendance, especially with remote work. Follow-up: does the pattern coincide with ACS work-from-home shares?
2. Contra Costa and Solano: high-band net balances became more negative by 16,428.3 and 18,288.0 respectively. Meaning: high-band resident-worker counts increasingly exceeded local high-band workplace counts. Caveat: WAC/RAC cannot show where these workers commute or whether the same individuals changed behavior. Follow-up: which OD destinations explain the balances?
3. Alameda: high-band net balance increased by 20,756.8, from −22,428.3 to −1,671.5. Meaning: its high-band workplace/residence balance moved closer to zero. Caveat: a county total can hide opposing tract patterns. Follow-up: which tracts account for the change, and does the pattern persist with endpoint comparisons?

These are descriptive associations within the nine counties and 2017–2023. They do not establish pandemic effects or confirm the hypothesis causally. Fixed nominal thresholds and changing workforce composition limit cross-year interpretation.

## Validation and reproducibility
The module rejects nulls, duplicate tract-year keys, missing years or counties, incomplete tract panels, malformed/mismatched GEOIDs, negative/fractional counts, and earnings-band totals inconsistent with WAC/RAC totals. It verifies that county aggregation preserves regional totals by band and year. No missing records are silently converted to zero here. Prior cleaning's zero-filling remains an upstream assumption.

Run from repository root:

```bash
python -m src.analysis.earnings_balance
python -m src.main analyze
python -m pytest -q
```

HF2a is wired into `run_analysis()` whenever WAC/RAC data exist. Full `python -m src.main` still needs the other project's raw inputs and network-based cleaning steps; it is not certified by this focused run.
