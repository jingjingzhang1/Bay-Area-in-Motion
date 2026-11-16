
"""HF2a checks: period weighting, aggregation and failure on incomplete input."""

import unittest
import pandas as pd

from src.analysis.earnings_balance import build_tables
from src.utils.config import BAY_AREA_COUNTIES, YEARS


def sample():
    rows = []
    for county in BAY_AREA_COUNTIES:
        for year in YEARS:
            row = dict(
                tract_geoid=county + '000100',
                county_fips=county,
                year=year,
                WAC=6 * (year - 2016),
                RAC=6
            )
            for i, band in enumerate(['CE01', 'CE02', 'CE03'], 1):
                row['WAC_' + band] = i * (year - 2016)
                row['RAC_' + band] = i
            rows.append(row)
    return pd.DataFrame(rows)


class TestEarningsBalance(unittest.TestCase):

    def test_period_means_and_changes(self):
        tables = build_tables(sample())
        periods = tables['hf2a_county_period_means']

        first = periods[
            (periods.county_fips == '06001') &
            (periods.earnings_band == 'CE01')
        ].set_index('period')

        self.assertEqual(first.loc['pre', 'mean_annual_net_jobs'], 1)
        self.assertEqual(first.loc['during', 'mean_annual_net_jobs'], 3.5)
        self.assertEqual(first.loc['post', 'mean_annual_net_jobs'], 5.5)

        changes = tables['hf2a_county_period_changes']

        self.assertTrue(
            changes.loc[
                changes.earnings_band == 'CE01',
                'post_minus_pre_net_jobs'
            ].eq(4.5).all()
        )

        self.assertEqual(len(tables['hf2a_county_annual']), 189)

    def test_invalid_input_fails(self):
        for problem in [
            'missing_year',
            'duplicate',
            'band_mismatch',
            'null'
        ]:
            with self.subTest(problem=problem):
                frame = sample()

                if problem == 'missing_year':
                    frame = frame.drop(index=0)

                if problem == 'duplicate':
                    frame = pd.concat([frame, frame.iloc[[0]]])

                if problem == 'band_mismatch':
                    frame.loc[0, 'WAC_CE01'] += 1

                if problem == 'null':
                    frame.loc[0, 'RAC_CE01'] = float('nan')

                with self.assertRaises(ValueError):
                    build_tables(frame)


if __name__ == '__main__':
    unittest.main()