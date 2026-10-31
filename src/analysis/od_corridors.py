"""Commuting flows and county-to-county corridors from the cleaned OD files."""
import pandas as pd

from src.utils.config import BAY_AREA_COUNTIES, TABLES_DIR, PRE_COVID_YEAR
from src.data.load_data import iter_od, OD_ID_COLS

BAY = list(BAY_AREA_COUNTIES)


def tract_flows(years, cache_file=TABLES_DIR / "od_tract_flows_by_year.csv"):
    """Commuters (S000) for every home tract / work tract pair and year. Cached after the first run."""
    if cache_file.exists():
        return pd.read_csv(cache_file, dtype=OD_ID_COLS)
    pieces = []
    for year in years:
        parts = [c.groupby(list(OD_ID_COLS), as_index=False)["S000"].sum() for c in iter_od(year)]
        t = pd.concat(parts).groupby(list(OD_ID_COLS), as_index=False)["S000"].sum()
        t.insert(0, "year", year)
        pieces.append(t)
    flows = pd.concat(pieces, ignore_index=True)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    flows.to_csv(cache_file, index=False)
    return flows


def county_flows(flows):
    return flows.groupby(["year", "h_county", "w_county"], as_index=False)["S000"].sum()


def county_corridors(flows):
    """Wide table of commuters per corridor (home county -> a different work county, both in the Bay Area)."""
    cty = county_flows(flows)
    inter = cty[cty.h_county.isin(BAY) & cty.w_county.isin(BAY) & (cty.h_county != cty.w_county)].copy()
    inter["corridor"] = inter.h_county.map(BAY_AREA_COUNTIES) + " to " + inter.w_county.map(BAY_AREA_COUNTIES)
    wide = inter.pivot(index="corridor", columns="year", values="S000").fillna(0)
    return wide.sort_values(wide.columns.max(), ascending=False)


def top_corridors(corr_wide, n=15):
    """Top n corridors in the latest year with % change from the first year and from 2019."""
    first, last = corr_wide.columns.min(), corr_wide.columns.max()
    top = corr_wide.head(n).copy()
    top[f"pct_change_{first}_{last}"] = ((top[last] / top[first] - 1) * 100).round(1)
    if PRE_COVID_YEAR in top.columns:
        top[f"pct_change_{PRE_COVID_YEAR}_{last}"] = ((top[last] / top[PRE_COVID_YEAR] - 1) * 100).round(1)
    return top


def top_tract_pairs(flows, year, n=20):
    """Largest tract-to-tract flows in one year (different tracts only)."""
    tr = flows[(flows.year == year) & (flows.h_tract != flows.w_tract)]
    return tr.nlargest(n, "S000")[["h_tract", "w_tract", "S000"]]


def cross_county_share(flows):
    """% of in-Bay commutes that cross a county line, by year."""
    cty = county_flows(flows)
    in_bay = cty[cty.h_county.isin(BAY) & cty.w_county.isin(BAY)]
    cross = in_bay[in_bay.h_county != in_bay.w_county].groupby("year")["S000"].sum()
    return (cross / in_bay.groupby("year")["S000"].sum() * 100).round(2).rename("pct_cross_county")
