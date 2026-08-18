from datetime import date, timedelta
import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from fetch_valuation import percentile_rank, summarize_rows, valuation_band


class ValuationTests(unittest.TestCase):
    def test_percentile_and_band(self):
        values = list(range(1, 101))
        self.assertEqual(percentile_rank(values, 20), 20.0)
        self.assertEqual(valuation_band(20), "very_low")
        self.assertEqual(valuation_band(50), "neutral")
        self.assertEqual(valuation_band(90), "very_high")

    def test_summarize_keeps_true_pe_history(self):
        end = date(2026, 8, 18)
        rows = []
        for i in range(2600):
            observed = end - timedelta(days=2599 - i)
            rows.append({"date": observed.isoformat(), "pe_ttm": 10 + (i % 100) / 10})
        item = summarize_rows("000300", "沪深300", rows, today=end)
        self.assertEqual(item["status"], "fresh")
        self.assertIsNotNone(item["percentile_10y"])
        self.assertGreater(item["observations_10y"], 2000)
        self.assertTrue(item["history_monthly_10y"])
        self.assertEqual(item["metric"], "滚动市盈率")


if __name__ == "__main__":
    unittest.main()
