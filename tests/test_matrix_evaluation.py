import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from evaluate_matrix_states import aggregate, settle_record


class MatrixEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.history = {
            "benchmark": {"rows": [
                {"date": "2026-08-18", "close": 100},
                {"date": "2026-08-19", "close": 101},
                {"date": "2026-08-20", "close": 102},
                {"date": "2026-08-21", "close": 103},
                {"date": "2026-08-24", "close": 104},
                {"date": "2026-08-25", "close": 105},
            ]},
            "assets": {"000001": {"rows": [
                {"date": "2026-08-18", "close": 10},
                {"date": "2026-08-19", "close": 10.3},
                {"date": "2026-08-20", "close": 10.4},
                {"date": "2026-08-21", "close": 10.5},
                {"date": "2026-08-24", "close": 10.7},
                {"date": "2026-08-25", "close": 10.9},
            ]}},
        }

    def test_bullish_direction_uses_excess_return(self):
        record = {
            "state_id": "x", "signal_date": "2026-08-18", "asset": "000001", "name": "样本",
            "matrix_direction": "bullish", "thesis_state": "confirmed", "evidence_state": "multi_layer_confirmed",
        }
        result = settle_record(record, self.history)
        t1 = result["horizons"]["t1"]
        self.assertTrue(t1["correct"])
        self.assertGreater(t1["directional_excess"], 0)

    def test_neutral_conflict_has_no_fake_hit_rate(self):
        record = {
            "state_id": "y", "signal_date": "2026-08-18", "asset": "000001", "name": "样本",
            "matrix_direction": "neutral", "thesis_state": "conflicted", "evidence_state": "conflict",
        }
        result = settle_record(record, self.history)
        self.assertIsNone(result["horizons"]["t1"]["correct"])
        self.assertIsNone(result["horizons"]["t1"]["directional_excess"])
        self.assertGreater(result["horizons"]["t1"]["absolute_excess"], 0)

    def test_small_sample_never_becomes_usable_readout(self):
        record = {
            "state_id": "z", "signal_date": "2026-08-18", "asset": "000001", "name": "样本",
            "matrix_direction": "bullish", "thesis_state": "emerging", "evidence_state": "partial_confirmation",
        }
        result = settle_record(record, self.history)
        summary = aggregate([result], "thesis_state")
        self.assertEqual(summary["emerging"]["horizons"]["t1"]["readout"], "insufficient_sample")
        self.assertEqual(summary["emerging"]["horizons"]["t1"]["directional_settled"], 1)


if __name__ == "__main__":
    unittest.main()
