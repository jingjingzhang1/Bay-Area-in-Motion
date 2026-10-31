"""Checks for missing estimates, identifier integrity and join behavior."""
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock

import pandas as pd

from src.analysis.daytime_population import county_daytime, tract_daytime, tract_net_change
from src.data.census_api import CensusClient, clean_counts, add_coverage
from src.data.clean_acs_county import clean_acs_county
from src.data.clean_acs_tract import clean_acs_tract


def wac_rac_table():
    return pd.DataFrame({"year": [2019, 2020], "tract_geoid": ["06001400100"] * 2,
                         "county_fips": ["06001"] * 2, "WAC": [120, 110], "RAC": [100, 100]})


def acs_table():
    return pd.DataFrame({"year": [2019], "county_fips": ["06001"], "population": [1000],
                         "workers_residence": [100], "work_from_home": [10], "workers_workplace": [130]})


class DaytimeTests(unittest.TestCase):
    def test_keeps_2020_and_computes_proxies(self):
        result = county_daytime(wac_rac_table(), acs_table()).set_index("year")
        self.assertEqual(result.loc[2019, "county_fips"], "06001")
        self.assertEqual(result.loc[2019, "daytime_proxy_lodes"], 1020)
        self.assertEqual(result.loc[2019, "daytime_proxy_acs"], 1030)
        self.assertEqual(result.loc[2019, "lodes_minus_acs"], -10)
        self.assertEqual(result.loc[2019, "work_from_home_pct"], 10)
        self.assertEqual(result.loc[2020, "net_jobs"], 10)
        self.assertTrue(pd.isna(result.loc[2020, "population"]))
        self.assertTrue(pd.isna(result.loc[2020, "daytime_proxy_lodes"]))

    def test_rejects_duplicate_tracts(self):
        frame = wac_rac_table()
        with self.assertRaisesRegex(ValueError, "Duplicate tract-year"):
            county_daytime(pd.concat([frame, frame.iloc[:1]]), acs_table())

    def test_rejects_duplicate_estimates(self):
        acs = acs_table()
        with self.assertRaises(Exception):
            county_daytime(wac_rac_table(), pd.concat([acs, acs]))

    def test_rejects_county_tract_mismatch(self):
        frame = wac_rac_table()
        frame.loc[0, "county_fips"] = "06013"
        with self.assertRaisesRegex(ValueError, "identifiers"):
            county_daytime(frame, acs_table())

    def test_tract_proxy_uses_fixed_population(self):
        pop = pd.DataFrame({"tract_geoid": ["06001400100"], "population": [800], "population_moe": [90],
                            "flag_population_under_500": [0], "flag_relative_moe_gt_50pct": [0]})
        result = tract_daytime(wac_rac_table(), pop).set_index("year")
        self.assertEqual(result.loc[2019, "daytime_proxy"], 820)
        self.assertEqual(result.loc[2020, "daytime_proxy"], 810)

    def test_tract_net_change(self):
        chg = tract_net_change(wac_rac_table(), 2019, 2020)
        self.assertEqual(chg.loc[0, "delta_net_jobs"], -10)
        self.assertEqual(chg.loc[0, "county_name"], "Alameda")


class CensusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

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

    def test_county_panel_years_moe_and_controlled_population(self):
        client = Mock()

        def table(year, dataset, params):
            self.assertNotEqual(year, 2020)
            county = params["for"].split(":")[1]
            row = {column: "100" for column in params["get"].split(",")}
            row["B01003_001M"] = "-555555555"           # controlled estimate: no numeric MOE
            row.update(NAME="County", state="06", county=county)
            return pd.DataFrame([row])

        client.table.side_effect = table
        out = self.root / "acs.csv"
        result = clean_acs_county(out, client=client)
        self.assertEqual(len(result), 63)                    # 9 counties x 7 years (no 2020)
        self.assertEqual(client.table.call_count, 63)
        self.assertEqual(result.year.min(), 2017)
        self.assertTrue(result.loc[result.year.eq(2017), "workers_workplace"].notna().all())
        self.assertTrue(result["population_moe"].isna().all())
        self.assertTrue(result["workers_workplace_moe"].notna().all())
        self.assertEqual(pd.read_csv(out, dtype={"county_fips": str}).county_fips.iloc[0], "06001")


class TractTests(unittest.TestCase):
    def test_reads_census_zip_and_flags_reliability(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        csv = ("GEO_ID,NAME,B01003_001E,B01003_001M\n"
               "Geography,Geographic Area Name,Estimate!!Total,Margin of Error!!Total\n"
               "1400000US06001400100,Tract 4001,3000,300\n"
               "1400000US06075017700,Tract 177,400,250\n"
               "1400000US06067000100,Sacramento tract,5000,100\n")
        zip_path = root / "acs.zip"
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("ACSDT5Y2023.B01003-Data.csv", csv)
        tracts = clean_acs_tract(zip_path, root / "out.csv", vital_signs_path=root / "none.csv")
        self.assertEqual(list(tracts.tract_geoid), ["06001400100", "06075017700"])
        self.assertEqual(list(tracts.flag_population_under_500), [0, 1])
        self.assertEqual(list(tracts.flag_relative_moe_gt_50pct), [0, 1])


if __name__ == "__main__":
    unittest.main()
