# Chiahao — ACS / LODES code PR handoff

**Project:** Bay Area in Motion (2017–2023) · Team 404: Static Not Found  
**Scope:** Chiahao's ACS County + ACS5 Tract + 2019/2023 LODES integration and figures.

## Intended team repository structure

- `src/data/prepare_county_acs.py` — read Census B01003/B08301/B08604 ZIP files, validate official estimates / MOE, join county LODES, output county panel and coverage QA.
- `src/data/prepare_tract_acs.py` — read ACS5 tract data / MTC reference / tract LODES summary; join 2023 residential population and MOE; output tract proxy with a fixed population baseline.
- `src/analysis/summarize_daytime_changes.py` — prepare report-ready summaries of 2017/2023 WFH and 2019/2023 fixed-baseline tract proxy changes.
- `src/visualization/plot_county_acs.py` — generate two county charts from processed data.
- `scripts/run_chiahao_pipeline.py` — run all four pieces in the correct order.
- `data/raw/chiahao/{county,tract}/` — relevant input snapshots and Census ZIP downloads for reproducibility; check team's Git LFS/.gitignore policy before pushing raw data.
- `data/processed/chiahao/` — output CSVs, audits and validation results.
- `reports/figures/chiahao/` — generated charts.
- `reports/early_results_chiahao.md` — Early Results draft (not yet merged into team report).
- `docs/CHIAHAO_SOURCE_NOTES.md` — source and caveats from prior handoff.
- `tests/test_chiahao_outputs.py` — minimal dataset QA.

**Run** from the repo root:

```bash
pip install -r requirements-chiahao.txt
python scripts/run_chiahao_pipeline.py
python -m unittest discover -s tests -p 'test_chiahao_outputs.py'
```

## Limitations to keep in the report

- 2020 **has no standard ACS 1-Year release**: preserve the gap in 2017–2023 ACS1 figures.
- Napa B08301 was not returned in the supplied 2021/2022 official downloaded tables: the result is blank, never zero.
- Census ACS1 B01003 County 90% MOE raw values are `*****` (controlled estimates), not numeric MOEs. ACS count MOEs must not be presented as uncertainties for computed ratios or proxies.
- Fixed 2023 ACS5 (2019–2023 reference period) resident population for the 2019 vs. 2023 tract proxy **isolates LODES net job-balance differences**. It is not a direct measurement of resident-population change across those years, nor a physical daytime headcount.
- WAC/RAC count jobs/covered employment, not exactly the same worker population as ACS. Comparisons are proxies.

## Before opening PR

1. Review actual team repo folder names, existing pipeline interfaces, current data files and `.gitignore`; do **not** overwrite teammates' modules or duplicate shared LODES data blindly.
2. Run commands above from a new branch (e.g. `chiahao-acs-population`), verify outputs and check `git status`.
3. Commit only the relevant reviewed files, push the branch and open a PR into protected `main`. Have another teammate approve and merge.
4. **Remaining deliverable:** the requested pre/post-COVID **population change map** is **not** automatically generated in this package. Prior 2019/2023 WAC/RAC net-commuting maps are separate and must not be presented as residential-population-change maps.
