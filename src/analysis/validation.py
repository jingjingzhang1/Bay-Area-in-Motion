"""Ballpark checks of the cleaned OD data against WAC/RAC and ACS."""
import pandas as pd

from src.utils.config import BAY_AREA_COUNTIES

BAY = list(BAY_AREA_COUNTIES)


def od_county_totals(flows):
    """OD commuters by work county (od_work) and by home county (od_home), per year."""
    work = flows[flows.w_county.isin(BAY)].groupby(["year", "w_county"])["S000"].sum()
    home = flows[flows.h_county.isin(BAY)].groupby(["year", "h_county"])["S000"].sum()
    out = pd.concat([work.rename("od_work"), home.rename("od_home")], axis=1)
    out.index.names = ["year", "county_fips"]
    return out.reset_index()


def validate_vs_wac_rac(od_totals, wac_rac):
    """OD totals divided by WAC (by workplace) and RAC (by residence). Expect slightly below 1,
    because OD 'main' leaves out workers who live outside California."""
    wr = wac_rac.groupby(["year", "county_fips"], as_index=False)[["WAC", "RAC"]].sum()
    val = od_totals.merge(wr, on=["year", "county_fips"], how="left")
    val["work_ratio"] = (val.od_work / val.WAC).round(3)
    val["home_ratio"] = (val.od_home / val.RAC).round(3)
    return val


def validate_vs_acs(od_totals, acs_county):
    """OD totals divided by ACS workers by workplace / residence. Expect about 0.8-1.0,
    because LODES leaves out self-employed workers. Also returns the county rank correlation."""
    acs = acs_county[["year", "county_fips", "workers_workplace", "workers_residence"]]
    val = od_totals.merge(acs, on=["year", "county_fips"], how="inner")
    val["work_vs_acs"] = (val.od_work / val.workers_workplace).round(3)
    val["home_vs_acs"] = (val.od_home / val.workers_residence).round(3)
    ranks = pd.DataFrame([
        {"year": year,
         "rank_corr_workplace": round(g.od_work.corr(g.workers_workplace, method="spearman"), 3),
         "rank_corr_residence": round(g.od_home.corr(g.workers_residence, method="spearman"), 3)}
        for year, g in val.groupby("year")
    ])
    return val, ranks
