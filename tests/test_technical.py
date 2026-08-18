import pathlib
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from build_technical import build, macd, ma60_state, rsi14, technical_for

BEIJING = timezone(timedelta(hours=8))


class TechnicalTests(unittest.TestCase):
    def series(self, rising=True):
        rows = []
        for i in range(90):
            close = 100 + i * 0.7 if rising else 160 - i * 0.6
            rows.append({
                "date": f"2026-05-{(i % 28)+1:02d}",
                "close": close,
                "high": close * 1.01,
                "low": close * 0.99,
                "volume": 1000 + i * 8,
            })
        return {"code": "603986", "name": "兆易创新", "last_date": "2026-08-18", "status": "fresh", "rows": rows}

    def test_rsi_and_ma60_for_rising_series(self):
        series = self.series(True)
        closes = [row["close"] for row in series["rows"]]
        self.assertGreater(rsi14(closes), 70)
        state = ma60_state(closes)
        self.assertEqual(state["position"], "above")
        self.assertEqual(state["direction"], "rising")

    def test_macd_state_is_explainable(self):
        closes = [100 + i * 0.2 for i in range(40)] + [108 + i * 1.2 for i in range(20)]
        value = macd(closes)
        self.assertEqual(value["state"], "bullish")
        self.assertIsNotNone(value["dif"])
        self.assertIsNotNone(value["dea"])

    def test_technical_output_never_contains_trade_action(self):
        item = technical_for(self.series(True))
        forbidden = {"buy", "sell", "position_size", "action", "target_price"}
        self.assertFalse(forbidden.intersection(item))
        self.assertIn(item["condition_state"], {"all_conditions", "partial_conditions", "conditions_not_met", "data_insufficient"})

    def test_state_changes_compare_previous_snapshot(self):
        history = {"generated_at": "2026-08-18T15:35:00+08:00", "assets": {"603986": self.series(True)}, "benchmark": self.series(True)}
        previous = {
            "assets": {
                "603986": {
                    "ma60": {"position": "below", "direction": "falling"},
                    "rsi_zone": "weak",
                    "macd": {"state": "bearish"},
                    "volume": {"state": "normal"},
                    "breakout_20d": "inside_range",
                    "condition_state": "conditions_not_met",
                }
            }
        }
        payload = build(history, previous=previous, now=datetime(2026, 8, 18, 16, 0, tzinfo=BEIJING))
        fields = {row["field"] for row in payload["state_changes"]}
        self.assertIn("ma60_position", fields)
        self.assertIn("macd", fields)
        self.assertIn("rsi_zone", fields)


if __name__ == "__main__":
    unittest.main()
