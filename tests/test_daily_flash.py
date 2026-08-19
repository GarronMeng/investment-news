import pathlib
import sys
import unittest
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from build_daily_flash import build, dimension_cards, theme_tracker
from fetch_catalysts import report_period
from fetch_global_markets import build as build_global


class DailyFlashTests(unittest.TestCase):
    def test_global_missing_is_unavailable_not_zero(self):
        def fail(_asset):
            raise RuntimeError("offline")
        payload = build_global(previous={}, fetcher=fail)
        self.assertEqual(payload["summary"]["fresh"], 0)
        self.assertTrue(all(row["value"] is None for row in payload["assets"]))
        self.assertTrue(all(row["status"] == "unavailable" for row in payload["assets"]))

    def test_report_period_for_august_is_half_year(self):
        code, label = report_period(date(2026, 8, 19))
        self.assertEqual(code, "20260630")
        self.assertEqual(label, "2026半年报")

    def test_dimension_cards_do_not_invent_missing_cross_asset_data(self):
        market = {"regime": {"score": -20, "code": "transition"}}
        cards = dimension_cards(market, {}, {"assets": []})
        lookup = {row["name"]: row for row in cards}
        self.assertIsNone(lookup["美股隔夜"]["score"])
        self.assertEqual(lookup["美股隔夜"]["label"], "数据不足")
        self.assertIsNone(lookup["汇率"]["score"])

    def test_theme_tracker_preserves_matrix_semantics(self):
        matrix = {
            "assets": {
                "603986": {"name": "兆易创新", "thesis_state": "no_directional_thesis", "evidence_state": "noise_or_no_edge", "matrix_direction": "neutral", "composite_score": -10, "layers": {"event": {"score": 0}, "technical": {"score": -20}, "industry": {"score": -15}}},
                "001309": {"name": "德明利", "thesis_state": "no_directional_thesis", "evidence_state": "noise_or_no_edge", "matrix_direction": "neutral", "composite_score": -15, "layers": {"event": {"score": 0}, "technical": {"score": -30}, "industry": {"score": -15}}},
            }
        }
        themes = theme_tracker(matrix)
        storage = next(row for row in themes if row["theme"] == "存储")
        self.assertEqual(storage["status"], "等待确认")
        self.assertEqual(storage["direction"], "neutral")

    def test_build_exposes_all_daily_sections(self):
        inputs = {
            "market_state": {"regime": {"label": "Transition", "code": "transition", "score": -10}, "breadth": {"advance_ratio": 0.4}, "sectors": {"leaders": [], "laggards": []}, "industry_flow": {}},
            "risk": {"score": 65, "label": "elevated"},
            "valuation": {}, "matrix": {"assets": {}, "ranking": [], "summary": {}},
            "global": {"assets": []}, "catalysts": {"events": []}, "ai": {"signals": []},
        }
        payload = build(inputs)
        for key in ("core_conclusion", "market", "sector_rotation", "global_markets", "key_events", "catalysts", "dimensions", "themes", "outlook", "matrix_focus"):
            self.assertIn(key, payload)
        forbidden = {"quantity", "position_size", "buy", "sell", "cost_basis", "stop_loss"}
        self.assertFalse(forbidden.intersection(payload))


if __name__ == "__main__":
    unittest.main()
