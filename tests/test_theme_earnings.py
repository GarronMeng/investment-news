import pathlib
import sys
import unittest
from datetime import date

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from fetch_theme_earnings import build, earnings_signal, theme_summary


class ThemeEarningsTests(unittest.TestCase):
    def test_earnings_signal_is_descriptive(self):
        self.assertEqual(earnings_signal(30, 50), "strong_growth")
        self.assertEqual(earnings_signal(5, 8), "positive_growth")
        self.assertEqual(earnings_signal(5, -8), "mixed")
        self.assertEqual(earnings_signal(-5, -8), "weak_growth")
        self.assertEqual(earnings_signal(None, 8), "unknown")

    def test_theme_summary_uses_reported_only(self):
        rows = [
            {"status": "reported", "earnings_signal": "positive_growth", "revenue_yoy_pct": 10, "net_profit_yoy_pct": 20},
            {"status": "reported", "earnings_signal": "weak_growth", "revenue_yoy_pct": -5, "net_profit_yoy_pct": -10},
            {"status": "scheduled", "earnings_signal": "not_reported", "revenue_yoy_pct": None, "net_profit_yoy_pct": None},
        ]
        summary = theme_summary(rows)
        self.assertEqual(summary["reported"], 2)
        self.assertEqual(summary["scheduled"], 1)
        self.assertEqual(summary["median_revenue_yoy_pct"], 2.5)
        self.assertEqual(summary["breadth"], "mixed")

    def test_build_never_fills_unreported_financials(self):
        earnings = pd.DataFrame([
            {
                "股票代码": "603986", "股票简称": "兆易创新",
                "营业总收入-营业总收入": 1000000000,
                "营业总收入-同比增长": 25.0,
                "净利润-净利润": 200000000,
                "净利润-同比增长": 30.0,
                "销售毛利率": 40.0,
                "所处行业": "半导体",
                "最新公告日期": "2026-08-19",
            }
        ])
        appointments = pd.DataFrame([
            {"股票代码": "001309", "股票简称": "德明利", "首次预约时间": "2026-08-28"}
        ])
        def fake_fetcher(today=None):
            return earnings, appointments, [], "20260630", "2026半年报"
        payload = build(previous={}, today=date(2026, 8, 19), fetcher=fake_fetcher)
        storage = next(x for x in payload["themes"] if x["theme"] == "存储")
        by_code = {x["code"]: x for x in storage["companies"]}
        self.assertEqual(by_code["603986"]["status"], "reported")
        self.assertEqual(by_code["603986"]["earnings_signal"], "strong_growth")
        self.assertEqual(by_code["001309"]["status"], "scheduled")
        self.assertIsNone(by_code["001309"]["net_profit_yoy_pct"])


if __name__ == "__main__":
    unittest.main()
