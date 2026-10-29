"""Run the full analysis from the project root:

    python -m src.main

Steps whose output already exists are skipped, so re-running is safe.
"""
from src.utils.config import YEARS, PROCESSED_DIR, DATA_DIR
from src.utils.helpers import make_output_dirs
from src.data.process_data import clean_crosswalk, clean_od
from src.data.load_data import load_wac_rac, load_acs_workers
from src.analysis import compute_metrics as cm
from src.visualization import plot_results as pr

WAC_RAC_FILE = PROCESSED_DIR / "bay_area_wac_rac_2017_2023_cleaned.csv"
ACS_RES_FILE = PROCESSED_DIR / "bay_area_acs1_B08301_workers_by_where_they_live_and_working_from_home_2018_2024.csv"
ACS_WORK_FILE = PROCESSED_DIR / "bay_area_acs1_B08604_workers_by_workplace_2018_2024.csv"


def main():
    make_output_dirs()
    print("Data folder:", DATA_DIR)

    # 1. Data cleaning
    clean_crosswalk()
    clean_od(YEARS)
    print(cm.od_row_log(YEARS))

    # 2. Corridors and trends
    flows = cm.tract_flows(YEARS)
    corr_wide = cm.county_corridors(flows)
    print(cm.top_corridors(corr_wide))
    print(cm.cross_county_share(flows))

    # 3. Validation
    od_totals = cm.od_county_totals(flows)
    if WAC_RAC_FILE.exists():
        wac_rac = load_wac_rac(WAC_RAC_FILE)
        val = cm.validate_vs_wacrac(od_totals, wac_rac)
        print(val.groupby("year")[["work_ratio", "home_ratio"]].agg(["min", "median", "max"]))
    else:
        wac_rac = None
        print("WAC/RAC file not found:", WAC_RAC_FILE)
    if ACS_RES_FILE.exists() and ACS_WORK_FILE.exists():
        val_acs = cm.validate_vs_acs(od_totals, load_acs_workers(ACS_RES_FILE, ACS_WORK_FILE))
        print(val_acs.groupby("year")[["work_vs_acs", "home_vs_acs"]].median())
    else:
        print("ACS files not found in", PROCESSED_DIR)

    # 4. Charts
    pr.plot_top_corridors(corr_wide)
    if wac_rac is not None:
        pr.plot_top_gain_loss(cm.tract_net_change(wac_rac, YEARS[0], YEARS[-1]), YEARS[0], YEARS[-1])
    print("Done. Tables in outputs/tables, figures in outputs/figures.")


if __name__ == "__main__":
    main()
