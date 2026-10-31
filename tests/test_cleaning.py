"""Regression checks for missing estimates, identifier integrity and join behavior."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import pandas as pd

from src.analysis.daytime_population import merge_counties
from src.data.census_api import CensusClient, clean_counts, add_coverage
from src.data import acs_counties


class CleaningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.lodes = self.root / "lodes.csv"
        self.population = self.root / "population.csv"
        self.residence = self.root / "residence.csv"
        self.workplace = self.root / "workplace.csv"
        pd.DataFrame({"year": [2019, 2020], "tract_geoid": ["06001400100"] * 2,
                      "county_fips": ["06001"] * 2, "WAC": [120, 110], "RAC": [100, 100]}).to_csv(self.lodes, index=False)
        pd.DataFrame({"year": [2019], "GEOID": ["06001"], "population": [1000]}).to_csv(self.population, index=False)
        pd.DataFrame({"year": [2019], "GEOID": ["06001"], "workers_residence": [100], "work_from_home": [10]}).to_csv(self.residence, index=False)
        pd.DataFrame({"year": [2019], "GEOID": ["06001"], "workers_workplace": [130]}).to_csv(self.workplace, index=False)

    def merge(self):
        return merge_counties(self.lodes, self.population, self.residence, self.workplace)

    def test_keeps_2020_and_computes_proxies(self):
        result = self.merge().set_index("year")
        self.assertEqual(result.loc[2019, "county_fips"], "06001")
        self.assertEqual(result.loc[2019, "daytime_population_LODES"], 1020)
        self.assertEqual(result.loc[2019, "daytime_population_acs"], 1030)
        self.assertEqual(result.loc[2019, "daytime_population_difference_2_metrics"], -10)
        self.assertEqual(result.loc[2019, "work_from_home_pct"], 10)
        self.assertEqual(result.loc[2020, "net_change"], 10)
        self.assertTrue(pd.isna(result.loc[2020, "population"]))
        self.assertTrue(pd.isna(result.loc[2020, "daytime_population_LODES"]))

    def test_rejects_duplicate_tracts(self):
        frame = pd.read_csv(self.lodes, dtype=str)
        pd.concat([frame, frame.iloc[:1]]).to_csv(self.lodes, index=False)
        with self.assertRaisesRegex(ValueError, "Duplicate tract-year"):
            self.merge()

    def test_rejects_duplicate_estimates(self):
        frame = pd.read_csv(self.population, dtype=str)
        pd.concat([frame, frame]).to_csv(self.population, index=False)
        with self.assertRaisesRegex(ValueError, "Duplicate county-year"):
            self.merge()

    def test_rejects_county_tract_mismatch(self):
        frame = pd.read_csv(self.lodes, dtype=str)
        frame.loc[0, "county_fips"] = "06013"
        frame.to_csv(self.lodes, index=False)
        with self.assertRaisesRegex(ValueError, "identifiers"):
            self.merge()

    def test_missing_sentinels_and_zero_denominators(self):
        frame = pd.DataFrame({"population": ["-666666666", "0"],
                              "workers_residence": ["0", "100"],
                              "work_from_home": ["0", "20"], "workers_workplace": [None, "150"]})
        clean_counts(frame, frame.columns)
        add_coverage(frame)
        self.assertTrue(pd.isna(frame.loc[0, "population"]))
        self.assertTrue(pd.isna(frame.loc[0, "work_from_home_pct"]))
        self.assertEqual(frame.loc[1, "population"], 0)
        self.assertEqual(frame.loc[1, "work_from_home_pct"], 20)

    def test_api_failure_does_not_become_missing_data_or_leak_key(self):
        client = CensusClient(self.root / "cache")
        client.api_key = "test-private-key"
        client.session = Mock()
        client.session.get.return_value.status_code = 503
        with self.assertRaisesRegex(RuntimeError, "HTTP 503") as error:
            client.table(2023, "acs/acs1", {"get": "NAME", "for": "county:001"})
        self.assertNotIn(client.api_key, str(error.exception))
        self.assertFalse(client.cache_dir.exists())

    def test_valid_api_table_is_reused_from_cache(self):
        client = CensusClient(self.root / "cache")
        client.session = Mock()
        client.session.get.return_value.status_code = 200
        client.session.get.return_value.json.return_value = [["NAME", "county"], ["Alameda", "001"]]
        params = {"get": "NAME", "for": "county:001"}
        first = client.table(2023, "acs/acs1", params)
        second = client.table(2023, "acs/acs1", params)
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(client.session.get.call_count, 1)

    def test_county_export_preserves_source_years_and_legacy_paths(self):
        client = Mock()

        def table(year, dataset, params):
            self.assertNotEqual(year, 2020)
            county = params["for"].split(":")[1]
            columns = params["get"].split(",")
            row = {column: "100" for column in columns}
            row.update(NAME="County", state="06", county=county)
            return pd.DataFrame([row])

        client.table.side_effect = table
        result = acs_counties.run(self.root, client=client)
        self.assertEqual(len(result), 63)
        self.assertEqual(client.table.call_count, 63)
        self.assertTrue(result.loc[result.year.eq(2017), "workers_workplace"].isna().all())
        self.assertTrue((self.root / acs_counties.RESIDENCE_FILE).is_file())
        workplace = pd.read_csv(self.root / acs_counties.WORKPLACE_FILE)
        self.assertEqual(len(workplace), 54)
        self.assertEqual(workplace.year.min(), 2018)


if __name__ == "__main__":
    unittest.main()
