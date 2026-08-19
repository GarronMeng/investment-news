import pathlib
import sys
import unittest
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from fetch_macro_calendar import build, normalize_macro_row, normalize_report_row


class MacroCalendarTests(unittest.TestCase):
    def test_macro_filters_low_importance_and_maps_channels(self):
        high = normalize_macro_row({
            "日期": "2026-08-20", "时间": "20:30", "地区": "美国",
            "事件": "美国7月CPI同比", "公布": None, "预期": 2.8, "前值": 2.7, "重要性": 3,
        })
        self.assertIsNotNone(high)
        self.assertEqual(high["category"], "inflation")
        self.assertIn("美债收益率", high["impact_channels"])
        low = normalize_macro_row({
            "日期": "2026-08-20", "时间": "10:00", "地区": "美国",
            "事件": "低重要性事件", "重要性": 1,
        })
        self.assertIsNone(low)

    def test_global_report_maps_theme_to_assets(self):
        universe = {"MU": {"name": "Micron", "themes": ["存储"]}}
        item = normalize_report_row({"股票代码": "MU", "交易所": "US", "财报期": "2026Q4"}, "2026-08-21", universe)
        self.assertEqual(item["type"], "global_earnings")
        self.assertIn("603986", item["assets"])
        self.assertIn("001309", item["assets"])

    def test_build_keeps_unknown_days_as_missing_not_fake_events(self):
        def fake_fetcher(today=None):
            return ([{
                "date": "2026-08-20", "time": "20:30", "type": "macro", "category": "inflation",
                "region": "美国", "title": "美国CPI", "importance": 3, "impact_channels": ["美债收益率"],
                "themes": [], "assets": [], "source": "test", "status": "scheduled",
            }], [], 11, 11)
        payload = build(previous={}, today=date(2026, 8, 19), fetcher=fake_fetcher)
        self.assertEqual(payload["summary"]["total"], 1)
        self.assertEqual(payload["summary"]["macro"], 1)
        self.assertEqual(payload["summary"]["global_earnings"], 0)


if __name__ == "__main__":
    unittest.main()
