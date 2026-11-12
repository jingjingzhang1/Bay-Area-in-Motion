"""Check the map's class boundaries and treatment of missing source values."""
import unittest

import numpy as np
import pandas as pd

from src.visualization.plot_population_change import classify, LABELS, population_change


class PopulationChangeTests(unittest.TestCase):
    def test_standard_change_sign_and_zero_current_population(self):
        counts = pd.DataFrame({"pop_2019": [1978, 100, 100, 3079],
                               "pop_2023": [2093, 80, 0, 3094]})
        expected = pd.Series([115 / 1978 * 100, -20.0, -100.0, 15 / 3079 * 100])
        pd.testing.assert_series_equal(population_change(counts), expected)

    def test_zero_baselines_and_invalid_counts_are_missing(self):
        counts = pd.DataFrame({"pop_2019": [0, 0, -99999, 100, None, np.inf, 100],
                               "pop_2023": [0, 5584, 100, -99999, 100, 100, np.inf]})
        self.assertTrue(population_change(counts).isna().all())

    def test_right_closed_boundaries_and_open_ended_extremes(self):
        values = pd.Series([-158.333, -20, -19.99, -10, -2, 0, 2, 10, 20, 84.4828])
        expected = [LABELS[i] for i in [0, 0, 1, 1, 2, 3, 3, 4, 5, 6]]
        self.assertEqual(classify(values).tolist(), expected)

    def test_sentinel_and_nonfinite_values_are_not_zero_change(self):
        result = classify(pd.Series([-99999, None, np.nan, np.inf, -np.inf, "bad", 0]))
        self.assertTrue(result.iloc[:6].isna().all())
        self.assertEqual(result.iloc[6], LABELS[3])


if __name__ == "__main__":
    unittest.main()
