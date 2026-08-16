from datetime import datetime, timedelta, timezone
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from fetch_market import build_payload, exchange_for, normalize_row


BEIJING = timezone(timedelta(hours=8))


class MarketQuoteTests(unittest.TestCase):
    def setUp(self):
        self.assets = [
            {"code": "603986", "name": "兆易创新"},
            {"code": "161226", "name": "国投白银LOF"},
        ]
        self.now = datetime.now(BEIJING).replace(hour=10, minute=0, second=0, microsecond=0)

    def test_exchange_mapping_handles_stocks_and_funds(self):
        self.assertEqual(exchange_for("603986"), "SSE")
        self.assertEqual(exchange_for("518880"), "SSE")
        self.assertEqual(exchange_for("161226"), "SZSE")

    def test_normalizes_chinese_quote_fields(self):
        quote = normalize_row(
            {"最新价": 500, "昨收": 490, "涨跌幅": 2.04, "今开": 492},
            "603986",
            "兆易创新",
            "fixture",
            self.now.isoformat(),
        )
        self.assertEqual(quote["price"], 500)
        self.assertEqual(quote["change_pct"], 2.04)
        self.assertEqual(quote["status"], "fresh")

    def test_fallback_and_stale_preservation_are_explicit(self):
        def batch(_assets, now=None):
            return {}, ["batch unavailable"]

        def fallback(asset, now=None):
            if asset["code"] == "603986":
                return normalize_row(
                    {"price": 500, "previous_close": 490},
                    asset["code"], asset["name"], "fallback", now.isoformat(), "low"
                )
            raise RuntimeError("symbol unavailable")

        previous_date = (self.now.date() - timedelta(days=1)).isoformat()
        previous = {
            "quotes": [{"code": "161226", "name": "国投白银LOF", "price": 1.6, "status": "fresh", "as_of": previous_date}]
        }
        payload = build_payload(self.assets, previous, self.now, batch, fallback)
        by_code = {row["code"]: row for row in payload["quotes"]}
        self.assertEqual(by_code["603986"]["status"], "fresh")
        self.assertEqual(by_code["161226"]["status"], "stale")
        self.assertIn("symbol unavailable", by_code["161226"]["error"])


if __name__ == "__main__":
    unittest.main()
