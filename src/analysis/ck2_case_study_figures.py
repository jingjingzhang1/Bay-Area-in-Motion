"""CK2: Plot workplace job trends for three case study areas."""

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

INPUT = Path("outputs/tables/ck2_case_studies.csv")
OUTPUT = Path("outputs/figures/fig_ck2_case_study_trends.png")

df = pd.read_csv(INPUT)

# Use 2019 as the baseline for each study area
baseline = (
    df[df["year"] == 2019]
    .set_index("area")["workplace_jobs"]
)

df["jobs_index"] = df.apply(
    lambda r: r["workplace_jobs"] / baseline[r["area"]] * 100,
    axis=1
)

fig, ax = plt.subplots(figsize=(10, 6))

for area, group in df.groupby("area"):
    group = group.sort_values("year")
    ax.plot(
        group["year"],
        group["jobs_index"],
        marker="o",
        linewidth=2,
        label=area
    )

ax.axhline(100, linestyle="--", color="gray", alpha=0.7)
ax.axvline(2019, linestyle=":", color="gray", alpha=0.6)

ax.set_title(
    "Workplace Job Trends in Three Bay Area Case Study Areas\n"
    "2017–2023 (2019 = 100)"
)
ax.set_xlabel("Year")
ax.set_ylabel("Workplace Jobs Index (2019 = 100)")
ax.set_xticks(range(2017, 2024))
ax.set_ylim(
    min(85, df["jobs_index"].min() - 2),
    max(115, df["jobs_index"].max() + 2)
)
ax.grid(alpha=0.25)
ax.legend()
fig.text(
    0.5, 0.01,
    "Source: LEHD LODES8 WAC. Study areas use approximate "
    "tract selections, not official downtown boundaries.",
    ha="center",
    fontsize=9
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
fig.tight_layout(rect=[0, 0.04, 1, 1])
fig.savefig(OUTPUT, dpi=180)
plt.close(fig)

print("Success! Created:", OUTPUT)
print("\n2023 index values:")
print(
    df[df["year"] == 2023][
        ["area", "jobs_index"]
    ].round(2).to_string(index=False)
)
