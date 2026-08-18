import pathlib
import sys
import unittest
from datetime import date
from unittest.mock import patch

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from fetch_history import align_to_benchmark_date, fresh, kind_for, refresh, sina_symbol_for, symbol_for
from build_features import feature_for
from build_decisions import event_score, market_score
from evaluate_signals import index_at_or_after


class ResearchEngineTests(unittest.TestCase):
    def test_symbol_kind_and_freshness_rules(self):
        self.assertEqual(symbol_for("603986"), "603986.SS")
        self.assertEqual(symbol_for("001309"), "001309.SZ")
        self.assertEqual(sina_symbol_for("161226"), "sz161226")
        self.assertEqual(sina_symbol_for("518880"), "sh518880")
        self.assertEqual(sina_symbol_for("603986"), "sh603986")
        self.assertEqual(kind_for("161226"), "lof")
        self.assertEqual(kind_for("518880"), "etf")
        self.assertEqual(kind_for("603986"), "stock")
        self.assertEqual(fresh("2026-08-14", today=date(2026, 8, 16)), "fresh")
        self.assertEqual(fresh("2026-08-01", today=date(2026, 8, 16)), "stale")

    def test_benchmark_alignment_prevents_one_session_old_false_fresh(self):
        item = {"status": "fresh", "last_date": "2026-08-17", "rows": [{"date": "2026-08-17", "close": 10}]}
        aligned = align_to_benchmark_date(item, "2026-08-18")
        self.assertEqual(aligned["status"], "stale")
        self.assertIn("benchmark 2026-08-18", aligned["staleness_reason"])
        same_day = align_to_benchmark_date({"status": "fresh", "last_date": "2026-08-18"}, "2026-08-18")
        self.assertEqual(same_day["status"], "fresh")

    def test_feature_engine_computes_relative_strength_without_inventing_turnover(self):
        rows = []
        for i in range(70):
            close = 100 + i
            rows.append({"date": f"2026-01-{(i % 28) + 1:02d}", "close": close, "volume": 1000 + i})
        series = {"code": "603986", "name": "兆易创新", "status": "fresh", "last_date": "2026-08-14", "rows": rows}
        feature = feature_for(series, {"ret_5d": 0.01, "ret_20d": 0.02})
        self.assertGreater(feature["ret_20d"], 0)
        self.assertGreater(feature["relative_strength_20d"], 0)
        self.assertGreater(feature["ma20_distance"], 0)
        self.assertIsNone(feature["turnover_z20"])
        self.assertEqual(feature["trend_state"], "bullish")

    def test_event_and_market_scores_are_transparent(self):
        bullish = [{"direction": "positive", "strength": 4}]
        bearish = [{"direction": "negative", "strength": 4}]
        self.assertEqual(event_score(bullish), 90)
        self.assertEqual(event_score(bearish), 10)
        score = market_score({
            "status": "fresh",
            "ret_20d": 0.1,
            "ma20_distance": 0.05,
            "relative_strength_20d": 0.04,
            "ret_5d": 0.03,
            "volume_z20": 1.5,
            "ret_1d": 0.02,
        })
        self.assertEqual(score, 90)

    def test_stock_history_uses_independent_sina_after_primary_error(self):
        rows = [
            {"date": f"2026-08-{day:02d}", "open": 10, "high": 11, "low": 9, "close": 10, "volume": 1, "amount": 100}
            for day in range(1, 21)
        ]
        warnings = []
        with patch("fetch_history.akshare_history", side_effect=RuntimeError("primary down")), patch(
            "fetch_history.sina_stock_history", return_value=rows
        ):
            result = refresh("603986", "兆易创新", "603986.SS", "stock", {}, warnings)
        self.assertEqual(result["source"], "新浪财经 via AKShare")
        self.assertIn("primary down", result["fallback_reason"])
        self.assertTrue(any("AKShare" in item for item in warnings))

    def test_fund_history_uses_independent_sina_after_primary_error(self):
        rows = [
            {"date": f"2026-08-{day:02d}", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "amount": None}
            for day in range(1, 21)
        ]
        warnings = []
        with patch("fetch_history.akshare_history", side_effect=RuntimeError("primary down")), patch(
            "fetch_history.sina_fund_history", return_value=rows
        ):
            result = refresh("161226", "国投白银LOF", "161226.SZ", "lof", {}, warnings)
        self.assertEqual(result["source"], "新浪财经 via AKShare")
        self.assertIn("primary down", result["fallback_reason"])
        self.assertTrue(any("AKShare" in item for item in warnings))

    def test_forward_index_uses_first_trading_observation_at_or_after_signal(self):
        rows = [
            {"date": "2026-08-13", "close": 10},
            {"date": "2026-08-14", "close": 11},
            {"date": "2026-08-17", "close": 12},
        ]
        self.assertEqual(index_at_or_after(rows, "2026-08-14"), 1)
        self.assertEqual(index_at_or_after(rows, "2026-08-15"), 2)


if __name__ == "__main__":
    unittest.main()
