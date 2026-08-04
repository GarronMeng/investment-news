import importlib.util
import pathlib
import unittest
from datetime import date, datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fetch_sentiment", ROOT / "scripts" / "fetch_sentiment.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SentimentRulesTest(unittest.TestCase):
    def test_numeric_helpers(self):
        self.assertEqual(MODULE.pct_change(110, 100), 10.0)
        self.assertEqual(MODULE.percentile_rank([10, 20, 30, 40], 30), 75.0)
        self.assertEqual(MODULE.zscore([5, 5, 5], 5), 0.0)

    def test_vix_thresholds(self):
        self.assertEqual(MODULE.classify_vix(14)[0], "calm")
        self.assertEqual(MODULE.classify_vix(22)[0], "elevated")
        self.assertEqual(MODULE.classify_vix(31)[0], "extreme")

    def test_margin_requires_change_and_position_for_heating(self):
        self.assertEqual(MODULE.classify_margin(None, None)[0], "building")
        self.assertEqual(MODULE.classify_margin(2.0, 1.2)[0], "heating")
        self.assertEqual(MODULE.classify_margin(2.0, 0.2)[0], "stable")
        self.assertEqual(MODULE.classify_margin(-1.2, -0.8)[0], "cooling")

    def test_failed_refresh_preserves_last_value_as_stale(self):
        previous = {
            "metrics": [{
                "id": "vix", "label": "VIX海外风险", "value": 21.5,
                "as_of": "2026-07-30", "status": "fresh", "level": "elevated",
                "state_label": "偏高", "tone": "warning",
            }]
        }
        kept = MODULE.preserve_or_unavailable(
            previous, "vix", "VIX海外风险", RuntimeError("network"), today=date(2026, 8, 4)
        )
        self.assertEqual(kept["value"], 21.5)
        self.assertEqual(kept["status"], "stale")
        self.assertEqual(kept["lag_days"], 5)

    def test_payload_does_not_fake_missing_metric(self):
        def fail_vix(today=None):
            raise RuntimeError("vix unavailable")

        def fail_margin(today=None):
            raise RuntimeError("margin unavailable")

        payload = MODULE.build_payload(
            previous={},
            now=datetime(2026, 8, 4, tzinfo=timezone.utc),
            vix_fetcher=fail_vix,
            margin_fetcher=fail_margin,
        )
        self.assertEqual(payload["metrics"][0]["status"], "unavailable")
        self.assertIsNone(payload["metrics"][1]["value"])
        self.assertEqual(len(payload["warnings"]), 2)


if __name__ == "__main__":
    unittest.main()
