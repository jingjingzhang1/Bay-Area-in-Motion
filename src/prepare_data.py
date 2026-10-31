"""Run Hanzhen's cleaning modules from the project root: python -m src.prepare_data --help."""
import argparse
from pathlib import Path

from src.data import acs_counties, acs_places, acs_blockgroups
from src.analysis.daytime_population import merge_counties
from src.utils.config import PROCESSED_DIR, FIGURES_DIR, TABLES_DIR


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["counties", "places", "blockgroups", "merge", "all"])
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument("--tables-dir", type=Path, default=TABLES_DIR)
    parser.add_argument("--figures-dir", type=Path, default=FIGURES_DIR)
    parser.add_argument("--lodes", type=Path, help="Existing cleaned tract WAC/RAC CSV (required for merge/all)")
    parser.add_argument("--force-refresh", action="store_true", help="Refresh cached Census responses")
    parser.add_argument("--plots", action="store_true", help="Also export jurisdiction/block-group coverage figures")
    args = parser.parse_args()
    if args.stage in ("merge", "all") and (args.lodes is None or not args.lodes.is_file()):
        parser.error("merge/all requires --lodes pointing to an existing cleaned tract WAC/RAC CSV")
    if args.stage in ("counties", "all"):
        acs_counties.run(args.processed_dir, force_refresh=args.force_refresh)
    if args.stage in ("places", "all"):
        _, roster, coverage, summary = acs_places.run(
            args.processed_dir / "acs1_jurisdiction_output", force_refresh=args.force_refresh)
        if args.plots:
            from src.visualization.plot_acs_coverage import plot_places
            plot_places(roster, coverage, summary, args.figures_dir / "acs_places")
    if args.stage in ("blockgroups", "all"):
        _, _, missing_pct = acs_blockgroups.run(
            args.processed_dir / "acs5_blockgroup_output", force_refresh=args.force_refresh)
        if args.plots:
            from src.visualization.plot_acs_coverage import plot_blockgroups
            plot_blockgroups(missing_pct, args.figures_dir / "acs_blockgroups")
    if args.stage in ("merge", "all"):
        merged = merge_counties(args.lodes, args.processed_dir / acs_counties.POPULATION_FILE,
                                args.processed_dir / acs_counties.RESIDENCE_FILE,
                                args.processed_dir / acs_counties.WORKPLACE_FILE)
        args.tables_dir.mkdir(parents=True, exist_ok=True)
        output = args.tables_dir / "bay_area_daytime_population_merged.csv"
        merged.to_csv(output, index=False)
        if args.plots:
            from src.visualization.plot_acs_coverage import plot_work_from_home
            plot_work_from_home(merged, args.figures_dir)
        print(f"Saved {len(merged)} county-year rows to {output}")


if __name__ == "__main__":
    main()
