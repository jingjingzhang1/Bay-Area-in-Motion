"""Prepare HY2a county/city panels and print a worked example.

Run from the repository root with ``py -m src.analysis.hy2a``.
City counts use LODES block-to-place assignments in the official crosswalk.
"""
import pandas as pd

from src.analysis.daytime_population import ACS_VALUES, county_daytime
from src.data.clean_wac_rac import raw_wac_rac_path
from src.data.load_data import load_acs_county, load_wac_rac
from src.utils.config import (
    BAY_AREA_COUNTIES, PROCESSED_DIR, RAW_XWALK, TABLES_DIR, YEARS,
)


def aggregate_blocks():
    """Aggregate primary jobs independently by workplace and residence."""
    crosswalk_parts = []
    for chunk in pd.read_csv(
        RAW_XWALK, usecols=["tabblk2020", "cty", "stplc"],
        dtype=str, chunksize=200_000,
    ):
        crosswalk_parts.append(chunk.loc[chunk["cty"].isin(BAY_AREA_COUNTIES)])
    crosswalk = pd.concat(crosswalk_parts, ignore_index=True)
    if crosswalk["tabblk2020"].duplicated().any():
        raise ValueError("Duplicate block IDs in crosswalk")
    print("1. Crosswalk columns (text):", crosswalk.columns.tolist())
    print(crosswalk.head(2).to_string(index=False))

    county_parts, city_parts = [], []
    for year in YEARS:
        county_sides, city_sides = [], []
        for kind in ["wac", "rac"]:
            block_column = "w_geocode" if kind == "wac" else "h_geocode"
            column = kind.upper()
            raw = pd.read_csv(
                raw_wac_rac_path(kind, year), usecols=[block_column, "C000"],
                dtype={block_column: str},
            )
            raw = raw.loc[raw[block_column].str[:5].isin(BAY_AREA_COUNTIES)]
            if raw[block_column].duplicated().any():
                raise ValueError(f"Duplicate {kind} blocks in {year}")
            if raw["C000"].isna().any() or raw["C000"].lt(0).any():
                raise ValueError(f"Invalid {kind} counts in {year}")
            joined = raw.merge(
                crosswalk, left_on=block_column, right_on="tabblk2020",
                how="left", validate="one_to_one", indicator=True,
            )
            if joined["_merge"].ne("both").any():
                raise ValueError(f"Unmatched {kind} blocks in {year}")
            # Match the project's 2020 block/tract county geography. The
            # crosswalk's county assignments can reflect boundary revisions.
            county = joined.groupby(joined[block_column].str[:5])["C000"].sum().rename(column)
            # Keep all place codes here, including outside-place codes, so job
            # totals reconcile before selecting the incorporated city roster.
            city = joined.groupby("stplc", dropna=False)["C000"].sum().rename(column)
            if county.sum() != raw["C000"].sum() or city.sum() != county.sum():
                raise ValueError(f"Aggregation lost jobs in {kind} {year}")
            county_sides.append(county)
            city_sides.append(city)
            if year == YEARS[0] and kind == "wac":
                print("\n2. Block workplace input joined to county/city IDs:")
                print(joined[[block_column, "C000", "cty", "stplc"]].head(3).to_string(index=False))
        county = pd.concat(county_sides, axis=1).fillna(0).astype("int64")
        city = pd.concat(city_sides, axis=1).fillna(0).astype("int64")
        county_parts.append(county.rename_axis("county_fips").reset_index().assign(year=year))
        city_parts.append(city.rename_axis("GEOID").reset_index().assign(year=year))
        print(f"  {year}: WAC={county.WAC.sum():,}, RAC={county.RAC.sum():,}; totals preserved")
    return pd.concat(county_parts, ignore_index=True), pd.concat(city_parts, ignore_index=True)


def add_measures(panel):
    """Use the same annual ACS population baseline for both proxies."""
    panel.loc[panel.year.eq(2020), ACS_VALUES] = float("nan")
    panel["net_jobs"] = panel.WAC - panel.RAC
    panel["daytime_proxy_lodes"] = panel.population + panel.net_jobs
    panel["daytime_proxy_acs"] = panel.population + panel.workers_workplace - panel.workers_residence
    panel["lodes_minus_acs"] = panel.daytime_proxy_lodes - panel.daytime_proxy_acs
    panel["lodes_minus_acs_pct"] = 100 * panel.lodes_minus_acs / panel.daytime_proxy_acs.where(panel.daytime_proxy_acs > 0)
    panel["work_from_home_pct"] = 100 * panel.work_from_home / panel.workers_residence.where(panel.workers_residence > 0)
    panel["missing_metrics"] = panel[ACS_VALUES].apply(
        lambda row: ", ".join(row.index[row.isna()]), axis=1,
    )
    panel["comparison_available"] = panel[ACS_VALUES + ["WAC", "RAC"]].notna().all(axis=1)
    panel["availability"] = panel["missing_metrics"].map(
        lambda value: f"Missing: {value}" if value else "All estimates available"
    )
    panel.loc[panel.year.eq(2020), "availability"] = "2020 standard ACS 1-year unavailable"
    return panel


def main():
    county_jobs, city_jobs = aggregate_blocks()
    # Independently reconcile the fresh block aggregation against the existing
    # tract aggregation before calculating either proxy.
    existing = load_wac_rac().groupby(["year", "county_fips"])[["WAC", "RAC"]].sum().sort_index()
    fresh = county_jobs.set_index(["year", "county_fips"])[["WAC", "RAC"]].sort_index()
    pd.testing.assert_frame_equal(fresh, existing, check_dtype=False)

    acs_county = load_acs_county()
    county = county_jobs.merge(acs_county, on=["year", "county_fips"], how="left", validate="one_to_one")
    county["county_name"] = county.county_fips.map(BAY_AREA_COUNTIES)
    county = add_measures(county)
    county["lodes_geography"] = "County prefix of 2020 block GEOID"
    # Also check the normal county analysis entry point's formulas.
    reference = county_daytime(load_wac_rac(), acs_county).set_index(["year", "county_fips"])
    for column in ["daytime_proxy_lodes", "daytime_proxy_acs", "lodes_minus_acs"]:
        pd.testing.assert_series_equal(county.set_index(["year", "county_fips"])[column].sort_index(), reference[column].sort_index())

    city_path = PROCESSED_DIR / "acs1_jurisdiction_output" / "bay_area_acs1_places_2017_2023.csv"
    acs_city = pd.read_csv(city_path, dtype={"GEOID": str, "state": str, "place": str})
    acs_city = acs_city.loc[acs_city.year.isin(YEARS) & acs_city.place_type.eq("incorporated")].copy()
    city = acs_city.merge(city_jobs, on=["year", "GEOID"], how="left", validate="one_to_one")
    if city[["WAC", "RAC"]].isna().any().any():
        raise ValueError("City roster has unmatched LODES place-years")
    city = add_measures(city)
    city.loc[city.place_returned.eq(False) & city.year.ne(2020), "availability"] = "Place not published in ACS 1-year"
    city["lodes_geography"] = "LODES v8 crosswalk block-to-place"

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    for label, panel, key in [("county", county, "county_fips"), ("city", city, "GEOID")]:
        if panel.duplicated([key, "year"]).any():
            raise ValueError(f"Duplicate {label}-year rows")
        if not panel.groupby(key).year.nunique().eq(len(YEARS)).all():
            raise ValueError(f"Incomplete {label}-year roster")
        output = TABLES_DIR / f"hy2a_{label}_2017_2023.csv"
        panel.sort_values([key, "year"]).to_csv(output, index=False, lineterminator="\n")
        print(f"\n3. {label.title()} result: {len(panel)} rows, {panel[key].nunique()} areas")
        print(panel.groupby("year").comparison_available.agg(["size", "sum"]).to_string())
        print("Saved", output)

    example = county.loc[county.county_name.eq("San Francisco") & county.year.isin([2019, 2023])]
    columns = ["year", "population", "WAC", "RAC", "workers_workplace", "workers_residence", "work_from_home", "daytime_proxy_lodes", "daytime_proxy_acs", "lodes_minus_acs", "lodes_minus_acs_pct", "work_from_home_pct"]
    print("\n4. Worked county example:")
    print(example[columns].round(2).to_string(index=False))
    print("\n5. City example (Alameda):")
    print(city.loc[city.jurisdiction_name.eq("Alameda city") & city.year.eq(2019), ["GEOID"] + columns].round(2).to_string(index=False))
    print("\nVerified unique geography-years, seven years per area, preserved job totals, county agreement, and explicit ACS gaps.")


if __name__ == "__main__":
    main()
