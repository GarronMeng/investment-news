import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from apply_matrix_sector_overrides import apply, exact_industry_layer


class MatrixSectorOverrideTests(unittest.TestCase):
    def setUp(self):
        self.market = {
            "sectors": {
                "leaders": [{"name": "半导体", "change_pct": 1.0}, {"name": "光学光电子", "change_pct": 3.0}],
                "laggards": [{"name": "通信设备", "change_pct": -2.0}],
            },
            "industry_flow": {
                "inflow": [{"name": "光学光电子", "change_pct": 3.0, "net_inflow": 10_000_000_000}],
                "outflow": [
                    {"name": "半导体", "change_pct": 1.0, "net_inflow": -15_000_000_000},
                    {"name": "通信设备", "change_pct": -2.0, "net_inflow": -12_000_000_000},
                ],
            },
        }

    def test_exact_mapping_does_not_pull_adjacent_taxonomy_sectors(self):
        layer = exact_industry_layer(["半导体"], self.market)
        self.assertEqual(layer["matches"], ["半导体"])
        self.assertNotIn("光学光电子", layer["evidence"])
        self.assertLess(layer["score"], 0)

    def test_explicit_empty_mapping_disables_industry_layer(self):
        layer = exact_industry_layer([], self.market)
        self.assertFalse(layer["available"])
        self.assertIsNone(layer["score"])
        self.assertEqual(layer["mapping_mode"], "explicit_none")

    def test_apply_overrides_only_assets_with_matrix_sectors(self):
        matrix = {
            "assets": {
                "1": {"code": "1", "name": "A", "layers": {"industry": {"available": True, "score": 99, "matches": ["光学光电子"]}}},
                "2": {"code": "2", "name": "B", "layers": {"industry": {"available": True, "score": 10, "matches": ["半导体"]}}},
            },
            "methodology": {},
        }
        watch = {"assets": [{"code": "1", "matrix_sectors": ["通信设备"]}, {"code": "2"}]}
        result = apply(matrix, watch, self.market)
        self.assertEqual(result["assets"]["1"]["layers"]["industry"]["matches"], ["通信设备"])
        self.assertEqual(result["assets"]["2"]["layers"]["industry"]["score"], 10)
        self.assertEqual(len(result["sector_mapping_audit"]), 1)


if __name__ == "__main__":
    unittest.main()
