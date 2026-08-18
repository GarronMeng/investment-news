import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from apply_matrix_sector_overrides import exact_industry_layer
from refine_decision_matrix import (
    apply_eligibility,
    conflict_metrics,
    recombine,
    refine,
    refined_evidence_state,
)


class MatrixRefinementTests(unittest.TestCase):
    def test_balanced_material_opposition_becomes_conflict(self):
        layers = {
            "event": {"available": False, "score": None},
            "technical": {"available": True, "score": -45},
            "relative_strength": {"available": True, "score": 70},
            "industry": {"available": True, "score": -25},
            "market_context": {"available": True, "score": 5},
        }
        metrics = conflict_metrics(layers)
        self.assertGreater(metrics["positive_mass"], 3)
        self.assertGreater(metrics["negative_mass"], 3)
        self.assertGreater(metrics["conflict_score"], 55)
        item = {
            "matrix_direction": "neutral",
            "composite_score": 0,
            "confluence": 10,
            "coverage": 75,
            "available_layers": 4,
            "opposing_weight_share": 0,
        }
        self.assertEqual(refined_evidence_state(item, metrics), "conflict")

    def test_one_sided_weak_evidence_remains_no_edge(self):
        layers = {
            "event": {"available": True, "score": 0},
            "technical": {"available": True, "score": 10},
            "relative_strength": {"available": True, "score": -12},
            "industry": {"available": True, "score": 8},
            "market_context": {"available": True, "score": -5},
        }
        metrics = conflict_metrics(layers)
        self.assertEqual(metrics["conflict_score"], 0.0)
        item = {
            "matrix_direction": "neutral",
            "composite_score": 1,
            "confluence": 2,
            "coverage": 100,
            "available_layers": 5,
            "opposing_weight_share": 0,
        }
        self.assertEqual(refined_evidence_state(item, metrics), "noise_or_no_edge")

    def test_refine_reclassifies_neutral_cancellation_and_tracks_change(self):
        payload = {
            "version": 1,
            "summary": {},
            "assets": {
                "000001": {
                    "code": "000001", "name": "样本", "priority": 5,
                    "base_bias": "neutral", "matrix_direction": "neutral",
                    "composite_score": 0, "coverage": 100, "confluence": 5,
                    "available_layers": 5, "opposing_weight_share": 0,
                    "evidence_state": "noise_or_no_edge", "thesis_state": "no_directional_thesis",
                    "layers": {
                        "event": {"available": True, "score": 0},
                        "technical": {"available": True, "score": -60},
                        "relative_strength": {"available": True, "score": 80},
                        "industry": {"available": True, "score": -30},
                        "market_context": {"available": True, "score": 10},
                    },
                }
            },
            "ranking": ["000001"], "state_changes": [], "methodology": {},
        }
        previous = {"assets": {"000001": {"evidence_state": "noise_or_no_edge", "thesis_state": "no_directional_thesis", "matrix_direction": "neutral"}}}
        result = refine(payload, previous)
        item = result["assets"]["000001"]
        self.assertEqual(item["evidence_state"], "conflict")
        self.assertEqual(item["thesis_state"], "conflicted")
        self.assertGreater(item["attention_score"], 80)
        self.assertTrue(any(x["field"] == "evidence_state" for x in result["state_changes"]))

    def test_hedge_excludes_a_share_industry_and_reweights(self):
        item = {
            "code": "518880", "group": "贵金属对冲",
            "layers": {
                "event": {"available": True, "score": 0, "confidence": "high"},
                "technical": {"available": True, "score": 40, "confidence": "high"},
                "relative_strength": {"available": True, "score": 30, "confidence": "high"},
                "industry": {"available": True, "score": 60, "confidence": "medium", "matches": ["油气开采及服务"]},
                "market_context": {"available": False, "score": None, "confidence": "none"},
            },
        }
        excluded = apply_eligibility(item)
        recombine(item)
        self.assertFalse(item["layers"]["industry"]["available"])
        self.assertTrue(any(x["layer"] == "industry" for x in excluded))
        expected = (25 * 0 + 30 * 40 + 20 * 30) / 75
        self.assertEqual(item["composite_score"], round(expected, 1))
        self.assertEqual(item["coverage"], 75.0)

    def test_stale_relative_strength_is_excluded_not_neutralized(self):
        item = {
            "code": "000001", "group": "科技核心",
            "layers": {
                "event": {"available": False, "score": None},
                "technical": {"available": True, "score": 60, "confidence": "high"},
                "relative_strength": {"available": True, "score": -80, "confidence": "medium"},
                "industry": {"available": False, "score": None},
                "market_context": {"available": False, "score": None},
            },
        }
        technical = {"assets": {"000001": {"source_status": "fresh", "data_quality": "usable"}}}
        features = {"assets": {"000001": {"status": "stale"}}}
        apply_eligibility(item, technical=technical, features=features)
        recombine(item)
        self.assertFalse(item["layers"]["relative_strength"]["available"])
        self.assertEqual(item["composite_score"], 60.0)
        self.assertEqual(item["coverage"], 30.0)

    def test_precise_matrix_sector_mapping_does_not_expand_news_taxonomy(self):
        market = {
            "sectors": {"leaders": [{"name": "半导体", "change_pct": 0.2}, {"name": "光学光电子", "change_pct": 3.0}], "laggards": []},
            "industry_flow": {
                "inflow": [{"name": "光学光电子", "change_pct": 3.0, "net_inflow": 10_000_000_000}],
                "outflow": [{"name": "半导体", "change_pct": 0.2, "net_inflow": -15_000_000_000}],
            },
        }
        layer = exact_industry_layer(["半导体"], market)
        self.assertEqual(layer["matches"], ["半导体"])
        self.assertNotIn("光学光电子", layer["evidence"])
        self.assertLess(layer["score"], 0)


if __name__ == "__main__":
    unittest.main()
