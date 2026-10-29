"""Functions for analysis: row logs, commuting flows, corridors and validation."""
import pandas as pd

from src.utils.config import BAY_AREA_COUNTIES, TABLES_DIR
from src.utils.helpers import count_rows
from src.data.load_data import raw_od_path, processed_od_path, iter_processed_od, ID_COLS

BAY = list(BAY_AREA_COUNTIES)


def od_row_log(years):
    """Raw vs kept row counts for each OD year (reported in the Data section)."""
    log_file = TABLES_DIR / "od_row_log.csv"
    log = pd.read_csv(log_file) if log_file.exists() else pd.DataFrame(columns=["year", "raw_rows", "kept_rows"])
    for year in years:
        if year in log["year"].values:
            continue
        log.loc[len(log)] = [year, count_rows(raw_od_path(year)), count_rows(processed_od_path(year))]
    log = log.sort_values("year").reset_index(drop=True)
    log["kept_pct"] = (log["kept_rows"] / log["raw_rows"] * 100).round(1)
    log.to_csv(log_file, index=False)
    return log


def tract_flows(years):
    """Commuters (S000) for every home tract / work tract pair and year. Cached to outputs/tables."""
    flow_file = TABLES_DIR / "od_tract_flows_by_year.csv"
    if flow_file.exists():
        return pd.read_csv(flow_file, dtype=ID_COLS)
    pieces = []
    for year in years:
        parts = [c.groupby(list(ID_COLS), as_index=False)["S000"].sum() for c in iter_processed_od(year)]
        t = pd.concat(parts).groupby(list(ID_COLS), as_index=False)["S000"].sum()
        t.insert(0, "year", year)
        pieces.append(t)
    flows = pd.concat(pieces, ignore_index=True)
    flows.to_csv(flow_file, index=False)
    return flows


def county_corridors(flows):
    """Wide table of commuters per corridor (home county -> different work county, both in the Bay Area) by year."""
    cty = flows.groupby(["year", "h_county", "w_county"], as_index=False)["S000"].sum()
    inter = cty[cty.h_county.isin(BAY) & cty.w_county.isin(BAY) & (cty.h_county != cty.w_county)].copy()
    inter["corridor"] = inter.h_county.map(BAY_AREA_COUNTIES) + " to " + inter.w_county.map(BAY_AREA_COUNTIES)
    wide = inter.pivot(index="corridor", columns="year", values="S000").fillna(0)
    return wide.sort_values(wide.columns.max(), ascending=False)


def top_corridors(corr_wide, n=15):
    """Top n corridors in the latest year with percent change from the first year and from 2019."""
    first, last = corr_wide.columns.min(), corr_wide.columns.max()
    top = corr_wide.head(n).copy()
    top[f"pct_change_{first}_{last}"] = ((top[last] / top[first] - 1) * 100).round(1)
    if 2019 in top.columns:
        top[f"pct_change_2019_{last}"] = ((top[last] / top[2019] - 1) * 100).round(1)
    top.to_csv(TABLES_DIR / "top_county_corridors_by_year.csv")
    return top


def cross_county_share(flows):
    """Percent of in-Bay commutes that cross a county line, by year."""
    cty = flows.groupby(["year", "h_county", "w_county"], as_index=False)["S000"].sum()
    in_bay = cty[cty.h_county.isin(BAY) & cty.w_county.isin(BAY)]
    cross = in_bay[in_bay.h_county != in_bay.w_county].groupby("year")["S000"].sum()
    return (cross / in_bay.groupby("year")["S000"].sum() * 100).round(2)


def od_county_totals(flows):
    """OD commuters by work county (od_work) and home county (od_home), by year."""
    work = flows[flows.w_county.isin(BAY)].groupby(["year", "w_county"])["S000"].sum()
    home = flows[flows.h_county.isin(BAY)].groupby(["year", "h_county"])["S000"].sum()
    out = pd.concat([work.rename("od_work"), home.rename("od_home")], axis=1)
    out.index.names = ["year", "county"]
    return out.reset_index()


def validate_vs_wacrac(od_totals, wac_rac):
    """Ratio of OD totals to WAC (by workplace) and RAC (by residence). Expect slightly below 1."""
    wr = wac_rac.copy()
    wr["county"] = wr["tract_geoid"].str[:5]
    wr = wr.groupby(["year", "county"], as_index=False)[["WAC", "RAC"]].sum()
    val = od_totals.merge(wr, on=["year", "county"], how="left")
    val["work_ratio"] = (val.od_work / val.WAC).round(3)
    val["home_ratio"] = (val.od_home / val.RAC).round(3)
    val.to_csv(TABLES_DIR / "validation_od_vs_wacrac.csv", index=False)
    return val


def validate_vs_acs(od_totals, acs):
    """Ratio of OD totals to ACS workers by workplace / residence (expect about 0.8-1.0)."""
    val = od_totals.merge(acs, on=["year", "county"], how="inner")
    val["work_vs_acs"] = (val.od_work / val.workers_by_workplace).round(3)
    val["home_vs_acs"] = (val.od_home / val.workers_by_residence).round(3)
    val.to_csv(TABLES_DIR / "validation_od_vs_acs.csv", index=False)
    return val


def tract_net_change(wac_rac, start, end):
    """Change in net jobs (WAC - RAC) per tract between two years."""
    t0 = wac_rac[wac_rac.year == start].set_index("tract_geoid")["net_change"]
    t1 = wac_rac[wac_rac.year == end].set_index("tract_geoid")["net_change"]
    chg = (t1 - t0).dropna().rename("delta_net_jobs").reset_index()
    chg["county_name"] = chg["tract_geoid"].str[:5].map(BAY_AREA_COUNTIES)
    return chg
