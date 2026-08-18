from datetime import datetime, timedelta, timezone
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from fetch_market_state import (
    breadth_from_rows,
    build_payload,
    daily_limit_pct,
    money_to_yuan,
    normalize_ths_industry,
    parse_tencent_indices,
    score_regime,
    ths_industry_money_to_yuan,
)

BEIJING = timezone(timedelta(hours=8))


class FakeFrame:
    def __init__(self, rows):
        self.rows = rows
        self.empty = not rows

    def iterrows(self):
        for i, row in enumerate(self.rows):
            yield i, FakeRow(row)


class FakeRow(dict):
    def to_dict(self):
        return dict(self)


class MarketStateTests(unittest.TestCase):
    def test_limit_band_rules(self):
        self.assertEqual(daily_limit_pct("603986", "兆易创新"), 10.0)
        self.assertEqual(daily_limit_pct("300308", "中际旭创"), 20.0)
        self.assertEqual(daily_limit_pct("688981", "中芯国际"), 20.0)
        self.assertEqual(daily_limit_pct("600000", "ST测试"), 5.0)
        self.assertEqual(daily_limit_pct("832000", "北交样本"), 30.0)

    def test_breadth_counts_and_seal_rate(self):
        rows = [
            {"代码": "600001", "名称": "甲", "涨跌幅": 10.0, "最新价": 11, "最高": 11, "昨收": 10, "成交额": 10},
            {"代码": "600002", "名称": "乙", "涨跌幅": 5.0, "最新价": 10.5, "最高": 11, "昨收": 10, "成交额": 20},
            {"代码": "300001", "名称": "丙", "涨跌幅": -20.0, "最新价": 8, "最高": 10, "昨收": 10, "成交额": 30},
            {"代码": "600003", "名称": "丁", "涨跌幅": 0.0, "最新价": 10, "最高": 10, "昨收": 10, "成交额": 40},
        ]
        breadth = breadth_from_rows(rows)
        self.assertEqual(breadth["total"], 4)
        self.assertEqual(breadth["up"], 2)
        self.assertEqual(breadth["down"], 1)
        self.assertEqual(breadth["flat"], 1)
        self.assertEqual(breadth["limit_up"], 1)
        self.assertEqual(breadth["touched_limit_up"], 2)
        self.assertEqual(breadth["broken_limit_up"], 1)
        self.assertEqual(breadth["limit_down"], 1)
        self.assertAlmostEqual(breadth["seal_rate"], 0.5)
        self.assertEqual(breadth["turnover"], 100.0)

    def test_tencent_parser(self):
        fields = ["0"] * 40
        fields[1] = "上证指数"
        fields[3] = "4000.00"
        fields[4] = "3960.00"
        fields[32] = "1.01"
        text = 'v_sh000001="' + "~".join(fields) + '";'
        rows = parse_tencent_indices(text, [("sh000001", "上证指数")])
        self.assertEqual(rows[0]["name"], "上证指数")
        self.assertEqual(rows[0]["price"], 4000.0)
        self.assertEqual(rows[0]["change_pct"], 1.01)

    def test_money_parser_and_ths_fallback_are_unit_safe(self):
        self.assertEqual(money_to_yuan("12.5亿"), 1_250_000_000)
        self.assertEqual(money_to_yuan("-3500万"), -35_000_000)
        self.assertEqual(ths_industry_money_to_yuan(12.5), 1_250_000_000)
        frame = FakeFrame([
            {"行业": "半导体", "行业-涨跌幅": 2.5, "净额": 12.5, "领涨股": "样本A"},
            {"行业": "煤炭", "行业-涨跌幅": -1.2, "净额": -3.0, "领涨股": "样本B"},
        ])
        sectors, flow = normalize_ths_industry(frame)
        self.assertEqual(sectors["leaders"][0]["name"], "半导体")
        self.assertEqual(sectors["laggards"][0]["name"], "煤炭")
        self.assertEqual(flow["inflow"][0]["net_inflow"], 1_250_000_000)
        self.assertEqual(flow["outflow"][0]["net_inflow"], -300_000_000)
        self.assertEqual(flow["inflow"][0]["source"], "同花顺 via AKShare")

    def test_regime_is_multi_factor_and_not_probability(self):
        breadth = {"advance_ratio": 0.72, "limit_up": 80, "limit_down": 5}
        indices = [{"change_pct": 1.2}, {"change_pct": 1.5}, {"change_pct": 0.8}]
        regime = score_regime(breadth, indices)
        self.assertEqual(regime["code"], "risk_on")
        self.assertGreater(regime["score"], 35)
        self.assertIn("不是收益概率", regime["methodology"])

    def test_zero_advance_ratio_is_valid_risk_off_data(self):
        breadth = {"advance_ratio": 0.0, "limit_up": 0, "limit_down": 100}
        indices = [{"change_pct": -2.0}, {"change_pct": -1.5}]
        regime = score_regime(breadth, indices)
        self.assertEqual(regime["code"], "risk_off")
        self.assertLess(regime["components"]["breadth"], -90)

    def test_state_change_alerts_are_generated_from_previous_snapshot(self):
        previous = {
            "breadth": {"advance_ratio": 0.30},
            "regime": {"code": "risk_off"},
        }
        rows = [
            {"代码": f"600{i:03d}", "名称": "样本", "涨跌幅": 1 if i < 7 else -1, "成交额": 1}
            for i in range(10)
        ]
        payload = build_payload(
            previous=previous,
            now=datetime(2026, 8, 18, 14, 0, tzinfo=BEIJING),
            a_share_rows=rows,
            indices=[{"change_pct": 0.8}, {"change_pct": 0.6}],
            sectors={"leaders": [], "laggards": [], "coverage": 1},
            industry_flow={"inflow": [], "outflow": [], "coverage": 1},
            etf_activity=[{"name": "ETF", "turnover": 1}],
        )
        self.assertTrue(any(item["type"] == "regime" for item in payload["alerts"]))
        self.assertTrue(any(item["type"] == "breadth" for item in payload["alerts"]))


if __name__ == "__main__":
    unittest.main()
