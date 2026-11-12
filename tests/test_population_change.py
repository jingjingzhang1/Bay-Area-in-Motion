"""Check the map's class boundaries and treatment of missing source values."""
import unittest

import numpy as np
import pandas as pd

from src.visualization.plot_population_change import classify, LABELS


class PopulationChangeTests(unittest.TestCase):
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
