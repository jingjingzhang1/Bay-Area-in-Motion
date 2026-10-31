"""Daytime population proxies at county and tract level.

County: two proxies per county and year
    LODES proxy = population + WAC - RAC
    ACS proxy   = population + workers by workplace - workers by residence
Tract: fixed 2023 ACS 5-year resident population P + year-specific WAC - RAC,
so changes over time reflect LODES net job flows only.
Both are commuting-based proxies, not counts of people physically present.
"""
import pandas as pd

from src.utils.config import BAY_AREA_COUNTIES

ACS_VALUES = ["population", "workers_residence", "work_from_home", "workers_workplace"]


def check_wac_rac(wac_rac):
    """Stop on invalid IDs, duplicate tract-years, or missing/negative job counts."""
    if (not wac_rac["county_fips"].isin(BAY_AREA_COUNTIES).all()
            or not wac_rac["tract_geoid"].str.fullmatch(r"\d{11}").fillna(False).all()
            or not wac_rac["tract_geoid"].str[:5].eq(wac_rac["county_fips"]).all()):
        raise ValueError("Invalid Bay Area tract/county identifiers in WAC/RAC input")
    if wac_rac.duplicated(["year", "tract_geoid"]).any():
        raise ValueError("Duplicate tract-year rows in WAC/RAC input")
    for column in ["WAC", "RAC"]:
        values = pd.to_numeric(wac_rac[column], errors="raise")
        if values.isna().any() or (values < 0).any():
            raise ValueError(f"Missing or negative {column} jobs")


def county_daytime(wac_rac, acs_county):
    """One row per county and year. Keeps every WAC/RAC year (including 2020, where ACS is blank)."""
    check_wac_rac(wac_rac)
    county = wac_rac.groupby(["year", "county_fips"], as_index=False)[["WAC", "RAC"]].sum()
    county = county.merge(acs_county[["year", "county_fips"] + ACS_VALUES],
                          on=["year", "county_fips"], how="left", validate="one_to_one")
    # No standard ACS 1-year values exist for 2020, even if an input file has some.
    county.loc[county["year"].eq(2020), ACS_VALUES] = float("nan")
    county["county_name"] = county["county_fips"].map(BAY_AREA_COUNTIES)
    county["net_jobs"] = county["WAC"] - county["RAC"]
    county["daytime_proxy_lodes"] = county["population"] + county["net_jobs"]
    county["daytime_proxy_acs"] = county["population"] + county["workers_workplace"] - county["workers_residence"]
    county["lodes_minus_acs"] = county["daytime_proxy_lodes"] - county["daytime_proxy_acs"]
    county["lodes_minus_acs_pct"] = (100 * county["lodes_minus_acs"] / county["daytime_proxy_acs"]).round(2)
    county["work_from_home_pct"] = 100 * county["work_from_home"] / county["workers_residence"].where(county["workers_residence"] > 0)
    columns = ["year", "county_fips", "county_name", "population", "WAC", "RAC", "net_jobs",
               "daytime_proxy_lodes", "workers_residence", "workers_workplace", "work_from_home",
               "work_from_home_pct", "daytime_proxy_acs", "lodes_minus_acs", "lodes_minus_acs_pct"]
    return county[columns].sort_values(["year", "county_name"]).reset_index(drop=True)


def wfh_change(county, start, end):
    """Work-from-home share by county in two years and the change in percentage points."""
    wide = county.pivot(index="county_name", columns="year", values="work_from_home_pct")
    out = wide[[start, end]].round(2)
    out.columns = [f"wfh_pct_{start}", f"wfh_pct_{end}"]
    out["change_pct_points"] = (out[f"wfh_pct_{end}"] - out[f"wfh_pct_{start}"]).round(2)
    return out.reset_index()


def tract_daytime(wac_rac, tract_population):
    """Tract proxy per year with a fixed resident population baseline (2023 ACS 5-year)."""
    check_wac_rac(wac_rac)
    pop = tract_population[["tract_geoid", "population", "population_moe",
                            "flag_population_under_500", "flag_relative_moe_gt_50pct"]]
    tract = wac_rac[["year", "tract_geoid", "county_fips", "WAC", "RAC"]].merge(
        pop, on="tract_geoid", how="left", validate="many_to_one")
    tract["county_name"] = tract["county_fips"].map(BAY_AREA_COUNTIES)
    tract["net_jobs"] = tract["WAC"] - tract["RAC"]
    tract["daytime_proxy"] = tract["population"] + tract["net_jobs"]
    tract["net_jobs_per_resident"] = (tract["net_jobs"] / tract["population"].where(tract["population"] >= 500)).round(4)
    return tract.sort_values(["tract_geoid", "year"]).reset_index(drop=True)


def tract_net_change(wac_rac, start, end):
    """Change in net jobs (WAC - RAC) per tract between two years."""
    net = wac_rac.assign(net_jobs=wac_rac["WAC"] - wac_rac["RAC"])
    t0 = net[net.year == start].set_index("tract_geoid")["net_jobs"]
    t1 = net[net.year == end].set_index("tract_geoid")["net_jobs"]
    chg = (t1 - t0).dropna().rename("delta_net_jobs").reset_index()
    chg["county_name"] = chg["tract_geoid"].str[:5].map(BAY_AREA_COUNTIES)
    return chg
