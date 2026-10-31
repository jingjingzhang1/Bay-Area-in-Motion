"""Fixed 2023 Bay Area place roster and 2017-2023 ACS 1-year coverage panel."""
import numpy as np
import pandas as pd
from pathlib import Path

from src.data.census_api import COUNTIES, STATE, VARIABLES, METRICS, CensusClient
from src.utils.config import PROCESSED_DIR

YEARS = list(range(2017, 2024))
ROSTER_YEAR = 2023
INCLUDE_CDPS = False


def run(output_dir=PROCESSED_DIR / "acs1_jurisdiction_output", *, client=None, force_refresh=False):
    OUTPUT_DIR = Path(output_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client = client or CensusClient(OUTPUT_DIR / "api_cache", force_refresh)
    place_names = client.table(ROSTER_YEAR, "acs/acs5", {
        "get": "NAME", "for": "place:*", "in": f"state:{STATE}",
    })
    memberships = []
    for county, county_name in COUNTIES.items():
        subdivisions = client.table(ROSTER_YEAR, "acs/acs5", {
            "get": "NAME", "for": "county subdivision:*",
            "in": f"state:{STATE} county:{county}",
        })
        county_parts = []
        for subdivision in subdivisions["county subdivision"]:
            county_parts.append(client.table(ROSTER_YEAR, "acs/acs5", {
                "get": "NAME", "for": "place/remainder (or part):*",
                "in": f"state:{STATE} county:{county} county subdivision:{subdivision}",
            }))
        parts = pd.concat(county_parts, ignore_index=True)
        parts = parts.rename(columns={"place/remainder (or part)": "place"})
        parts = parts.loc[parts["place"].ne("99999"), ["state", "place"]].drop_duplicates()
        parts["county_name"] = county_name
        memberships.append(parts)
        print(f"Roster: {county_name}, {len(parts)} places")
    membership = pd.concat(memberships, ignore_index=True)
    membership = membership.groupby(["state", "place"], as_index=False).agg(
        county_name=("county_name", lambda values: "; ".join(sorted(set(values))))
    )
    roster = place_names.merge(membership, on=["state", "place"], validate="one_to_one")
    roster["jurisdiction_name"] = roster["NAME"].str.replace(", California", "", regex=False)
    roster["place_type"] = np.where(
        roster["jurisdiction_name"].str.contains(r"\bCDP\b", regex=True), "CDP", "incorporated"
    )
    if not INCLUDE_CDPS:
        roster = roster.loc[roster["place_type"].eq("incorporated")].copy()
    roster["GEOID"] = roster["state"] + roster["place"]
    roster = roster.sort_values(["county_name", "jurisdiction_name"]).reset_index(drop=True)
    assert not roster.empty
    assert roster["GEOID"].is_unique
    print(f"{len(roster)} jurisdictions in the fixed {ROSTER_YEAR} roster.")

    year_frames = []
    for year in YEARS:
        if year == 2020:
            print("2020: standard ACS 1-year estimates not released; retaining explicit gaps.")
            continue
        frame = client.table(year, "acs/acs1", {
            "get": "NAME," + ",".join(VARIABLES),
            "for": "place:*", "in": f"state:{STATE}",
        })
        frame["GEOID"] = frame["state"] + frame["place"]
        frame = frame.loc[frame["GEOID"].isin(roster["GEOID"])].copy()
        frame["year"] = year
        frame["place_returned"] = True
        frame = frame.rename(columns={"NAME": "acs_name", **VARIABLES})
        for metric in METRICS:
            numeric = pd.to_numeric(frame[metric], errors="coerce")
            frame[metric] = numeric.mask(numeric < 0)
        year_frames.append(frame[["year", "GEOID", "acs_name", "place_returned"] + METRICS])
        print(f"{year}: {len(frame)} roster places returned.")

    observations = pd.concat(year_frames, ignore_index=True)
    assert not observations.duplicated(["year", "GEOID"]).any()
    panel = pd.MultiIndex.from_product(
        [YEARS, roster["GEOID"]], names=["year", "GEOID"]
    ).to_frame(index=False)
    panel = panel.merge(roster, on="GEOID", how="left", validate="many_to_one")
    panel = panel.merge(observations, on=["year", "GEOID"], how="left", validate="one_to_one")
    panel["place_returned"] = panel["place_returned"].eq(True)
    panel["work_from_home_pct"] = (
        100 * panel["work_from_home"] / panel["workers_residence"].where(panel["workers_residence"] > 0)
    )
    panel["missing_metrics"] = panel[METRICS].apply(
        lambda row: "; ".join(row.index[row.isna()]), axis=1
    )
    panel["availability"] = np.select(
        [
            panel["year"].eq(2020),
            ~panel["place_returned"],
            panel[METRICS].isna().any(axis=1),
        ],
        [
            "2020 ACS 1-year not released",
            "Place not published in ACS 1-year",
            "One or more estimates missing",
        ],
        default="All estimates available",
    )
    panel = panel.sort_values(["county_name", "jurisdiction_name", "year"]).reset_index(drop=True)
    assert len(panel) == len(roster) * len(YEARS)
    assert panel.loc[panel["year"].eq(2020), METRICS].isna().all().all()

    identity = ["year", "GEOID", "state", "place", "county_name", "jurisdiction_name", "NAME", "place_type"]
    panel.to_csv(OUTPUT_DIR / "bay_area_acs1_places_2017_2023.csv", index=False)
    for label, values in {
        "population": ["population"],
        "B08301": ["workers_residence", "work_from_home", "work_from_home_pct"],
        "B08604": ["workers_workplace"],
    }.items():
        panel[identity + values + ["availability"]].to_csv(
            OUTPUT_DIR / f"bay_area_acs1_places_{label}_2017_2023.csv", index=False
        )
    roster.to_csv(OUTPUT_DIR / "bay_area_place_roster_2023.csv", index=False)
    coverage = panel[identity + ["place_returned", "availability", "missing_metrics"]].copy()
    # Replaces the old coverage CSV at the same path on every run.
    estimate_status_columns = []
    for metric in METRICS:
        status_column = f"{metric}_status"
        estimate_status_columns.append(status_column)
        coverage[status_column] = np.select(
            [panel["year"].eq(2020), ~panel["place_returned"], panel[metric].isna()],
            ["2020 not released", "Place not published", "Missing estimate"],
            default="Available",
        )
    coverage.to_csv(OUTPUT_DIR / "jurisdiction_year_coverage.csv", index=False)

    coverage.loc[coverage["availability"].ne("All estimates available")].to_csv(
        OUTPUT_DIR / "missing_jurisdiction_years.csv", index=False
    )
    summary = panel.groupby(["year", "availability"]).size().unstack(fill_value=0).reindex(YEARS, fill_value=0)
    summary.to_csv(OUTPUT_DIR / "coverage_summary_by_year.csv")
    panel.groupby("year")[METRICS].agg(lambda values: values.isna().sum()).reindex(YEARS).to_csv(
        OUTPUT_DIR / "missing_estimates_by_year.csv"
    )
    return panel, roster, coverage, summary
