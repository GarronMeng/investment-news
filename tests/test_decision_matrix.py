import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from build_decision_matrix import (
    build,
    combine_layers,
    industry_layer,
    market_context_layer,
    thesis_state,
)


class DecisionMatrixTests(unittest.TestCase):
    def test_missing_layer_is_excluded_not_zero(self):
        layers = {
            "event": {"available": False, "score": None},
            "technical": {"available": True, "score": 80},
            "relative_strength": {"available": True, "score": 60},
            "industry": {"available": False, "score": None},
            "market_context": {"available": True, "score": -20},
        }
        composite, coverage, confluence, count, opposing = combine_layers(layers)
        expected = (30 * 80 + 20 * 60 + 10 * -20) / 60
        self.assertAlmostEqual(composite, round(expected, 1))
        self.assertEqual(count, 3)
        self.assertEqual(coverage, 60.0)
        self.assertGreater(confluence, 0)
        self.assertGreater(opposing, 0)

    def test_hedge_asset_excludes_a_share_market_context(self):
        asset = {"group": "贵金属对冲"}
        layer = market_context_layer(
            asset,
            {"regime": {"code": "risk_off"}, "breadth": {"advance_ratio": 0.2}},
            {"score": 90},
        )
        self.assertFalse(layer["available"])
        self.assertIsNone(layer["score"])

    def test_industry_absence_is_not_neutral(self):
        asset = {"industries": ["bio"]}
        market = {
            "sectors": {"leaders": [{"name": "银行", "change_pct": 2.0}], "laggards": []},
            "industry_flow": {"inflow": [], "outflow": []},
        }
        layer = industry_layer(asset, market)
        self.assertFalse(layer["available"])
        self.assertIsNone(layer["score"])

    def test_contradiction_requires_opposite_direction_with_evidence(self):
        self.assertEqual(thesis_state("bullish", "bearish", "partial_confirmation"), "contradicted")
        self.assertEqual(thesis_state("bullish", "neutral", "conflict"), "under_test")
        self.assertEqual(thesis_state("neutral", "bullish", "multi_layer_confirmed"), "emerging")

    def test_build_produces_ranked_assets_without_private_fields(self):
        watch = {
            "assets": [
                {
                    "code": "000001", "name": "样本", "group": "科技核心", "role": "测试",
                    "priority": 5, "industries": ["semi"],
                }
            ]
        }
        decisions = {
            "decisions": [
                {
                    "asset": "000001", "name": "样本", "bias": "bullish", "event_count": 1,
                    "event_score": 90, "evidence_mode": "event_plus_market", "as_of": "2026-08-18",
                    "confirmation": ["确认A"], "invalidation": ["失效A"],
                }
            ]
        }
        technical = {
            "source_generated_at": "2026-08-18T15:00:00+08:00",
            "assets": {
                "000001": {
                    "data_quality": "usable",
                    "ma60": {"position": "above", "direction": "rising"},
                    "macd": {"state": "bullish"},
                    "rsi14": 60, "rsi_zone": "strong",
                    "volume": {"state": "normal"}, "breakout_20d": "new_high_20d",
                }
            },
        }
        features = {
            "assets": {
                "000001": {"status": "fresh", "relative_strength_5d": 0.08, "relative_strength_20d": 0.15}
            }
        }
        market = {
            "regime": {"code": "risk_on"},
            "breadth": {"advance_ratio": 0.68},
            "sectors": {"leaders": [{"name": "半导体", "change_pct": 2.5}], "laggards": []},
            "industry_flow": {"inflow": [{"name": "半导体", "change_pct": 2.5, "net_inflow": 3_000_000_000}], "outflow": []},
        }
        payload = build(watch, decisions, technical, features, market, {"score": 35})
        item = payload["assets"]["000001"]
        self.assertEqual(payload["ranking"], ["000001"])
        self.assertEqual(item["matrix_direction"], "bullish")
        self.assertIn(item["thesis_state"], {"confirmed", "supported"})
        forbidden = {"quantity", "position_size", "buy", "sell", "cost_basis", "stop_loss"}
        self.assertFalse(forbidden.intersection(item))
        self.assertGreater(item["coverage"], 90)


if __name__ == "__main__":
    unittest.main()
