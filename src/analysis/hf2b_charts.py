from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Project root
ROOT = Path(__file__).resolve().parents[2]

# Load HF2a data
df = pd.read_csv(
	ROOT / "outputs/tables/hf2a_county_period_means.csv",
	dtype={"county_fips": str}
)

# Sum net jobs across the nine Bay Area counties
summary = (
	df.groupby(["earnings_band", "period"])["mean_annual_net_jobs"]
	.sum()
	.unstack("period")
)

periods = ["pre", "during", "post"]

labels = {
	"CE01": "Low: <= $1,250/month",
	"CE02": "Middle: $1,251-$3,333/month",
	"CE03": "High: > $3,333/month",
}

fig, ax = plt.subplots(figsize=(10, 6))

for band, label in labels.items():
	values = summary.loc[band, periods]
	ax.plot(
		range(3),
		values,
		marker="o",
		linewidth=2,
		markersize=7,
		label=label,
	)

ax.axhline(0, color="gray", linestyle="--", linewidth=1)

ax.set_title(
	"Bay Area Net Jobs by Earnings Band, 2017-2023",
	fontsize=14
)
ax.set_ylabel("Mean Annual Net Jobs (WAC - RAC)")
ax.set_xticks(
	range(3),
	["Pre (2017-19)", "During (2020-21)", "Post (2022-23)"]
)
ax.legend(title="Monthly Earnings")
ax.grid(axis="y", alpha=0.25)

fig.tight_layout()

output = ROOT / "outputs/figures"
output.mkdir(parents=True, exist_ok=True)

fig.savefig(
	output / "hf2b_earnings_trends.png",
	dpi=300,
	bbox_inches="tight"
)

plt.close(fig)

print("Saved: outputs/figures/hf2b_earnings_trends.png")

# Figure 2: High-earnings net jobs by county
county = df[df["earnings_band"] == "CE03"].copy()

county_chart = county.pivot(
    index="county_name",
    columns="period",
    values="mean_annual_net_jobs"
)

county_chart = county_chart[["pre", "post"]]
county_chart = county_chart.sort_values("post")

fig2, ax2 = plt.subplots(figsize=(11, 7))

y = range(len(county_chart))
ax2.barh(
    [i - 0.2 for i in y],
    county_chart["pre"],
    height=0.4,
    label="Pre (2017–19)"
)
ax2.barh(
    [i + 0.2 for i in y],
    county_chart["post"],
    height=0.4,
    label="Post (2022–23)"
)

ax2.set_yticks(list(y))
ax2.set_yticklabels(county_chart.index)
ax2.axvline(0, color="black", linewidth=0.8)
ax2.set_xlabel("Mean Annual Net Jobs (WAC − RAC)")
ax2.set_title("High-Earnings Net Jobs by Bay Area County")
ax2.legend()
ax2.grid(axis="x", alpha=0.2)

fig2.tight_layout()
fig2.savefig(
    ROOT / "outputs/figures/hf2b_high_earnings_counties.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close(fig2)

print("Saved: outputs/figures/hf2b_high_earnings_counties.png")
