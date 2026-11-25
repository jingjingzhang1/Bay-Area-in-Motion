# CK1b: Final Job Center Analysis

## Method

We classify Bay Area census tracts using the ratio of workplace jobs (WAC) to resident jobs (RAC).

Our baseline uses three categories:

- **Job Center:** WAC/RAC ≥ 1.25
- **Bedroom Community:** WAC/RAC ≤ 0.80
- **Balanced Area:** Between 0.80 and 1.25

We chose these thresholds to identify areas with at least 25% more workplace jobs than resident jobs, while using a reciprocal cutoff for bedroom communities.

We also tested two alternative scenarios: Lenient (1.10/0.90) and Strict (1.50/0.67).

## Results

Under the baseline, Job Centers decreased from 343 tracts in 2017 to 337 in 2023. Their share declined from 19.43% to 19.09%.

The lenient scenario showed a decline from 380 to 369 Job Centers, while the strict scenario showed a decline from 288 to 285.

All three scenarios show a small decline. This suggests that the direction of the trend is relatively stable across different thresholds, although the number of Job Centers depends on the classification rule.

## Interpretation and Limitations

Our findings suggest that the overall share of Job Centers remained relatively stable between 2017 and 2023.

However, the WAC/RAC ratio measures the balance of workplace and resident jobs, not the actual daytime population. Tracts with very few jobs may also have unstable ratios.

In addition, a small regional change may hide important changes in individual neighborhoods.

Future analysis should examine specific Job Centers and test whether minimum job-count requirements affect the results.

**Source:** LEHD LODES8 WAC/RAC, 2017–2023.