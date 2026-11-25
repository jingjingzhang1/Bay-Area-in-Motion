"""CK2: Bay Area workplace job concentration, 2017–2023."""

import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

INPUT = Path("outputs/tables/ck1a_job_center_typology.csv")
TABLE = Path("outputs/tables/ck2_concentration_trends.csv")
FIGURE = Path("outputs/figures/fig_ck2_concentration_trends.png")

df = pd.read_csv(INPUT)
results = []

for year, group in sorted(df.groupby("year")):
    jobs = group["WAC"]
    total = jobs.sum()
    n_top = math.ceil(len(jobs) * 0.10)

    top_share = jobs.nlargest(n_top).sum() / total * 100
    hhi = ((jobs / total) ** 2).sum() * 10000

    results.append({
        "year": int(year),
        "total_jobs": int(total),
        "top_10_share_pct": top_share,
        "hhi": hhi,
    })

result = pd.DataFrame(results)

TABLE.parent.mkdir(parents=True, exist_ok=True)
FIGURE.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(TABLE, index=False)

fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

axes[0].plot(
    result["year"], result["top_10_share_pct"],
    marker="o", linewidth=2, color="#2474a6"
)
axes[0].set_ylabel("Top 10% Job Share (%)")
axes[0].set_title("Share of Jobs in Top 10% of Census Tracts")
axes[0].grid(alpha=0.25)

axes[1].plot(
    result["year"], result["hhi"],
    marker="o", linewidth=2, color="#dc7645"
)
axes[1].set_ylabel("HHI (0–10,000 scale)")
axes[1].set_xlabel("Year")
axes[1].set_title("Workplace Job Concentration (HHI)")
axes[1].grid(alpha=0.25)

for ax in axes:
    ax.axvline(2019, linestyle="--", color="gray", alpha=0.6)
    ax.set_xticks(result["year"])

fig.suptitle(
    "Bay Area Workplace Job Concentration, 2017–2023",
    fontsize=14
)
fig.tight_layout()
fig.savefig(FIGURE, dpi=180)
plt.close(fig)

print(result.round(2).to_string(index=False))
print("\nSaved:", TABLE)
print("Saved:", FIGURE)
