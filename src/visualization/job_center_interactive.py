import json
from pathlib import Path
import pandas as pd

# 1. Read existing classification data
df = pd.read_csv(
    "outputs/tables/ck1a_job_center_typology.csv",
    dtype={"tract_geoid": str}
)
df["tract_geoid"] = df["tract_geoid"].str.zfill(11)

# 2. Read census tract boundaries
path = "data/raw/vital_signs/Vital_Signs__Population_-_Tracts_20261028.geojson"
with open(path) as f:
    geo = json.load(f)

# 3. Match classifications to map areas
lookup = {
    (r.tract_geoid, str(r.year)): r.tract_type
    for r in df.itertuples(index=False)
}

features = []
for f in geo["features"]:
    tract = str(f["properties"]["tract_geoid"]).zfill(11)
    categories = {
        str(y): lookup.get((tract, str(y)), "No data")
        for y in range(2017, 2024)
    }
    features.append({
        "type": "Feature",
        "geometry": f["geometry"],
        "properties": {
            "tract": tract,
            "categories": categories
        }
    })

map_data = {"type": "FeatureCollection", "features": features}

# 4. Build interactive Leaflet map
html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Bay Area Job Center Map</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
body { font-family: Arial, sans-serif; margin: 20px; }
#map { height: 75vh; width: 100%; background: #f1f5f7; }
.controls { margin: 15px 0; }
.legend { margin: 12px 0; }
.legend span { margin-right: 18px; }
.dot { display: inline-block; width: 12px; height: 12px; margin-right: 5px; }
</style>
</head>
<body>
<h2>Bay Area Job Center Classification, 2017–2023</h2>
<p>Explore how census tract classifications change over time.</p>

<div class="controls">
<label for="year">Year: <strong id="yearLabel">2023</strong></label>
<input id="year" type="range" min="2017" max="2023" value="2023" step="1">
<label style="display:block;margin-top:12px">
<input id="changesOnly" type="checkbox">
Highlight Classification Changes (2017–2023)
</label>
<small>When selected: red = changed, gray = unchanged.</small>
<div id="changeSummary"></div>
</div>

<div id="categoryLegend" class="legend">
<span><i class="dot" style="background:#e76f51"></i>Job Center</span>
<span><i class="dot" style="background:#e9c46a"></i>Balanced Area</span>
<span><i class="dot" style="background:#2a9d8f"></i>Bedroom Community</span>
</div>

<div id="changeLegend" class="legend" style="display:none">
<span><i class="dot" style="background:#d62828"></i>Changed Classification</span>
<span><i class="dot" style="background:#cbd5e1"></i>Unchanged</span>
</div>
<div id="map"></div>
<p><small>Source: LEHD LODES8 WAC/RAC; Bay Area Census Tracts.
Classification: CK1a baseline.</small></p>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const data = __MAP_DATA__;
const nChanged = data.features.filter(f =>
  f.properties.categories["2017"] !== f.properties.categories["2023"]
).length;
document.getElementById("changeSummary").textContent =
  nChanged + " of " + data.features.length + " tracts changed classification.";
let year = "2023";
const colors = {
  "Job Center": "#e76f51",
  "Balanced Area": "#e9c46a",
  "Bedroom Community": "#2a9d8f"
};

const map = L.map("map").setView([37.8, -122.2], 9);


function style(feature) {
  const p = feature.properties;
  const category = p.categories[year];
  const changed = p.categories["2017"] !== p.categories["2023"];
  const highlight = document.getElementById("changesOnly").checked;

  return {
    fillColor: highlight
      ? (changed ? "#d62828" : "#cbd5e1")
      : (colors[category] || "#cccccc"),
    color: highlight && changed ? "#7f1d1d" : "#555555",
    weight: highlight && changed ? 1.1 : 0.4,
    fillOpacity: highlight ? (changed ? 0.85 : 0.25) : 0.7
  };
}

const layer = L.geoJSON(data, {
  style: style,
  onEachFeature: function(feature, area) {
    area.on("click", function() {
      const p = feature.properties;
      const current = p.categories[year];
      area.bindPopup(
        "<b>Census Tract:</b> " + p.tract +
        "<br><b>Year:</b> " + year +
        "<br><b>Category:</b> " + current +
        "<br><b>2017:</b> " + p.categories["2017"] +
        "<br><b>2023:</b> " + p.categories["2023"]
      ).openPopup();
    });
  }
}).addTo(map);

map.fitBounds(layer.getBounds());

document.getElementById("changesOnly").addEventListener("change", function() {
  layer.setStyle(style);
  document.getElementById("categoryLegend").style.display =
    this.checked ? "none" : "block";
  document.getElementById("changeLegend").style.display =
    this.checked ? "block" : "none";
});

document.getElementById("year").addEventListener("input", function(e) {
  year = e.target.value;
  document.getElementById("yearLabel").textContent = year;
  layer.setStyle(style);
  layer.closePopup();
});
</script>
</body>
</html>
"""


# Reduce coordinate precision to make the HTML smaller.
def round_coordinates(value):
    if isinstance(value, list):
        return [round_coordinates(v) for v in value]
    if isinstance(value, float):
        return round(value, 5)
    return value

for feature in map_data["features"]:
    feature["geometry"]["coordinates"] = round_coordinates(
        feature["geometry"]["coordinates"]
    )

html = html.replace(
    "__MAP_DATA__",
    json.dumps(map_data, separators=(",", ":"))
)

output = Path("docs/maps/job_center_classification.html")
output.write_text(html, encoding="utf-8")

print("Success! Created:", output)
print("Census tracts:", len(features))
print("Years: 2017–2023")
