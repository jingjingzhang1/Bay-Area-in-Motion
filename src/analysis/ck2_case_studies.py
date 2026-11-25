"""CK2: Exploratory workplace job case studies."""

import json
import math
from pathlib import Path

import pandas as pd

GEO = Path(
    "data/raw/vital_signs/"
    "Vital_Signs__Population_-_Tracts_20261028.geojson"
)
CSV = Path("outputs/tables/ck1a_job_center_typology.csv")
OUTPUT = Path("outputs/tables/ck2_case_studies.csv")

areas = {
    "Downtown SF": (37.790, -122.405, 2.0),
    "Downtown San Jose": (37.335, -121.889, 2.0),
    "Dublin/Pleasanton": (37.681, -121.895, 5.0),
}

def distance_km(lat1, lon1, lat2, lon2):
    r = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))

with open(GEO) as f:
    features = json.load(f)["features"]

df = pd.read_csv(CSV, dtype={"tract_geoid": str})
df["tract_geoid"] = df["tract_geoid"].str.zfill(11)

results = []

for name, (lat, lon, radius) in areas.items():
    ids = []

    for feature in features:
        points = [
            point
            for polygon in feature["geometry"]["coordinates"]
            for ring in polygon
            for point in ring
        ]

        center_lon = (
            min(p[0] for p in points)
            + max(p[0] for p in points)
        ) / 2
        center_lat = (
            min(p[1] for p in points)
            + max(p[1] for p in points)
        ) / 2

        if distance_km(lat, lon, center_lat, center_lon) <= radius:
            ids.append(feature["properties"]["tract_geoid"])

    selected = df[df["tract_geoid"].isin(ids)]

    for year, group in selected.groupby("year"):
        results.append({
            "area": name,
            "year": int(year),
            "tracts": group["tract_geoid"].nunique(),
            "workplace_jobs": int(group["WAC"].sum()),
            "job_centers": int(
                (group["tract_type"] == "Job Center").sum()
            ),
        })

result = pd.DataFrame(results)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(OUTPUT, index=False)

print("=== Case Study Results: 2019 vs 2023 ===")

for name in areas:
    x = result[result["area"] == name]
    before = x[x["year"] == 2019].iloc[0]
    after = x[x["year"] == 2023].iloc[0]

    change = (
        (after["workplace_jobs"] / before["workplace_jobs"] - 1) * 100
        if before["workplace_jobs"] > 0 else float("nan")
    )

    print(f"\n{name}")
    print("Tracts:", int(before["tracts"]))
    print("2019 jobs:", int(before["workplace_jobs"]))
    print("2023 jobs:", int(after["workplace_jobs"]))
    print(f"Change: {change:+.2f}%")
    print(
        "Job Centers:",
        int(before["job_centers"]),
        "->",
        int(after["job_centers"])
    )

print("\nSaved:", OUTPUT)
