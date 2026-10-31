"""Run the whole project from the project root.

    python -m src.main                 # clean -> analyze -> figures
    python -m src.main clean           # only the data cleaning step
    python -m src.main analyze         # tables in outputs/tables
    python -m src.main figures         # charts in outputs/figures
    python -m src.main clean --extras  # also city (place) and block-group ACS coverage

Each step skips work whose output already exists and prints MISSING for an input
that has not been downloaded yet, so a partial run still finishes.
"""
import argparse

from src.utils.config import (
    YEARS, PRE_COVID_YEAR, DATA_DIR, TABLES_DIR, RAW_XWALK, RAW_ACS5_TRACT_ZIP,
    WAC_RAC_TRACTS, ACS_COUNTY, ACS_TRACT_POPULATION, od_path,
)
from src.utils.helpers import make_output_dirs


def missing(path, what):
    if path.exists():
        return False
    print(f"MISSING {what}: {path} (see README 'Getting the data')")
    return True


# ---------------------------------------------------------------- 1. clean
def run_cleaning(extras=False, force_refresh=False):
    from src.data.clean_od import clean_crosswalk, clean_od, od_row_log
    from src.data.clean_acs_county import clean_acs_county
    from src.data.clean_acs_tract import clean_acs_tract

    print("\n== Cleaning: LODES crosswalk and OD ==")
    if not missing(RAW_XWALK, "LODES crosswalk"):
        clean_crosswalk()
    clean_od(YEARS)
    print(od_row_log(YEARS, TABLES_DIR / "od_row_log.csv"))

    print("\n== Cleaning: LODES WAC/RAC ==")
    from src.data.clean_wac_rac import clean_wac_rac
    if WAC_RAC_TRACTS.exists():
        print(f"Skipping {WAC_RAC_TRACTS.name} (already cleaned)")
    else:
        _, log = clean_wac_rac(YEARS)
        if len(log):
            log.to_csv(TABLES_DIR / "wac_rac_row_log.csv", index=False)
            print(log)

    print("\n== Cleaning: ACS county (Census API) ==")
    if ACS_COUNTY.exists() and not force_refresh:
        print(f"Skipping {ACS_COUNTY.name} (already cleaned; use --force-refresh to download again)")
    else:
        clean_acs_county(force_refresh=force_refresh)

    print("\n== Cleaning: ACS tract population ==")
    if not missing(RAW_ACS5_TRACT_ZIP, "ACS 5-year tract B01003 download"):
        clean_acs_tract()

    if extras:
        from src.data.clean_acs_places import clean_acs_places
        from src.data.clean_acs_blockgroups import clean_acs_blockgroups
        from src.visualization.plot_acs_coverage import plot_places, plot_blockgroups
        from src.utils.config import FIGURES_DIR
        print("\n== Cleaning: ACS places and block groups (coverage) ==")
        _, roster, coverage, summary = clean_acs_places(force_refresh=force_refresh)
        plot_places(roster, coverage, summary, FIGURES_DIR / "acs_places_coverage")
        _, _, missing_pct = clean_acs_blockgroups(force_refresh=force_refresh)
        plot_blockgroups(missing_pct, FIGURES_DIR / "acs_blockgroups_coverage")


# ---------------------------------------------------------------- 2. analyze
def run_analysis():
    from src.data.load_data import load_wac_rac, load_acs_county
    from src.analysis import od_corridors as od
    from src.analysis import validation as val
    from src.analysis import daytime_population as day

    results = {}
    if all(od_path(y).exists() for y in YEARS):
        print("\n== Analysis: commuting corridors ==")
        flows = od.tract_flows(YEARS)
        corr = od.county_corridors(flows)
        top = od.top_corridors(corr)
        top.to_csv(TABLES_DIR / "od_top_county_corridors.csv")
        od.top_tract_pairs(flows, YEARS[-1]).to_csv(TABLES_DIR / f"od_top_tract_pairs_{YEARS[-1]}.csv", index=False)
        od.cross_county_share(flows).to_csv(TABLES_DIR / "od_cross_county_share.csv")
        print(top)
        results.update(corridors=corr, od_totals=val.od_county_totals(flows))
    else:
        print("MISSING cleaned OD files; run `python -m src.main clean` first")

    wac_rac = load_wac_rac() if WAC_RAC_TRACTS.exists() else None
    acs = load_acs_county() if ACS_COUNTY.exists() else None

    if "od_totals" in results:
        print("\n== Analysis: validation ==")
        if wac_rac is not None:
            check = val.validate_vs_wac_rac(results["od_totals"], wac_rac)
            check.to_csv(TABLES_DIR / "validation_od_vs_wac_rac.csv", index=False)
            print(check.groupby("year")[["work_ratio", "home_ratio"]].agg(["min", "median", "max"]))
        if acs is not None:
            check, ranks = val.validate_vs_acs(results["od_totals"], acs)
            check.to_csv(TABLES_DIR / "validation_od_vs_acs.csv", index=False)
            print(check.groupby("year")[["work_vs_acs", "home_vs_acs"]].median())
            print(ranks)

    if wac_rac is not None and acs is not None:
        print("\n== Analysis: county daytime population ==")
        county = day.county_daytime(wac_rac, acs)
        county.to_csv(TABLES_DIR / "daytime_county.csv", index=False)
        day.wfh_change(county, YEARS[0], YEARS[-1]).to_csv(TABLES_DIR / "daytime_county_wfh_change.csv", index=False)
        results["county"] = county
    if wac_rac is not None:
        chg = day.tract_net_change(wac_rac, YEARS[0], YEARS[-1])
        chg.to_csv(TABLES_DIR / f"daytime_tract_net_change_{YEARS[0]}_{YEARS[-1]}.csv", index=False)
        results["tract_change"] = chg
        if ACS_TRACT_POPULATION.exists():
            import pandas as pd
            tract_pop = pd.read_csv(ACS_TRACT_POPULATION, dtype={"tract_geoid": str, "county_fips": str})
            day.tract_daytime(wac_rac, tract_pop).to_csv(TABLES_DIR / "daytime_tract.csv", index=False)
    return results


# ---------------------------------------------------------------- 3. figures
def run_figures(results):
    from src.visualization import plot_od, plot_acs

    print("\n== Figures ==")
    if "corridors" in results:
        print(plot_od.plot_top_corridors(results["corridors"]))
    if "tract_change" in results:
        print(plot_od.plot_tract_gain_loss(results["tract_change"], YEARS[0], YEARS[-1]))
    if "county" in results:
        print(plot_acs.plot_wfh_share(results["county"]))
        print(plot_acs.plot_lodes_vs_acs(results["county"], YEARS[-1]))


def main():
    parser = argparse.ArgumentParser(description="Bay Area in Motion pipeline")
    parser.add_argument("step", nargs="?", default="all", choices=["all", "clean", "analyze", "figures"])
    parser.add_argument("--extras", action="store_true", help="also clean place and block-group ACS coverage")
    parser.add_argument("--force-refresh", action="store_true", help="download Census API tables again")
    args = parser.parse_args()

    make_output_dirs()
    print("Data folder:", DATA_DIR)
    if args.step in ("all", "clean"):
        run_cleaning(args.extras, args.force_refresh)
    if args.step in ("all", "analyze", "figures"):
        results = run_analysis()
        if args.step in ("all", "figures"):
            run_figures(results)
    print("\nDone. Tables in outputs/tables, figures in outputs/figures.")


if __name__ == "__main__":
    main()
