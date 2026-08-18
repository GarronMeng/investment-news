import pathlib
import sys
import unittest
from datetime import datetime, timedelta, timezone

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_risk_score import build, risk_label


class RiskScoreTests(unittest.TestCase):
    def fixture(self):
        valuation = {"indices": {"000300": {"percentile_10y": 80, "status": "fresh"}}}
        state = {
            "regime": {"code": "narrow_risk_on"},
            "breadth": {"advance_ratio": 0.42},
            "indices": [{"change_pct": 0.5}, {"change_pct": 0.2}],
        }
        technical = {
            "benchmark": {
                "data_quality": "usable",
                "ma60": {"position": "below", "direction": "falling"},
                "macd": {"state": "bearish"},
                "rsi_zone": "neutral",
            }
        }
        sentiment = {
            "metrics": [
                {"id": "margin_balance", "status": "fresh", "change_5d_pct": 2.0, "zscore_20d": None},
                {"id": "vix", "status": "fresh", "value": 25, "percentile_20d": 85},
            ]
        }
        return valuation, state, technical, sentiment

    def test_risk_label_thresholds(self):
        self.assertEqual(risk_label(20), "low")
        self.assertEqual(risk_label(45), "balanced")
        self.assertEqual(risk_label(60), "elevated")
        self.assertEqual(risk_label(75), "high")

    def test_build_is_weighted_and_explainable(self):
        valuation, state, technical, sentiment = self.fixture()
        payload = build(
            valuation, state, technical, sentiment,
            now=datetime(2026, 8, 18, 22, tzinfo=timezone(timedelta(hours=8))),
        )
        self.assertGreater(payload["score"], 60)
        self.assertEqual(payload["coverage"], 100.0)
        self.assertEqual(set(payload["components"]), {
            "valuation", "market_structure", "trend", "leverage", "overseas", "concentration"
        })
        self.assertTrue(payload["drivers"])
        self.assertIn(payload["label"], {"elevated", "high"})

    def test_missing_inputs_reduce_coverage_not_fake_values(self):
        payload = build({}, {}, {}, {}, now=datetime.now(timezone.utc))
        self.assertIsNone(payload["score"])
        self.assertEqual(payload["coverage"], 0.0)
        self.assertEqual(payload["label"], "insufficient")
        self.assertTrue(all(not x["available"] for x in payload["components"].values()))


if __name__ == "__main__":
    unittest.main()
