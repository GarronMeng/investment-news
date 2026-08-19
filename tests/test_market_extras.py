import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from fetch_market_extras import future_underlying, index_spots, preserve
from augment_daily_flash_extras import augment


class MarketExtrasTests(unittest.TestCase):
    def test_future_underlying_only_exact_supported_indices(self):
        self.assertEqual(future_underlying("沪深300指数2609"), "沪深300")
        self.assertEqual(future_underlying("中证1000指数2609"), "中证1000")
        self.assertIsNone(future_underlying("10年期国债2609"))

    def test_index_spots_uses_real_values(self):
        market = {"indices": [{"name": "沪深300", "price": 4500.5}, {"name": "恒生指数", "price": 25000}]}
        spots = index_spots(market)
        self.assertEqual(spots["沪深300"], 4500.5)

    def test_preserve_marks_old_data_stale(self):
        previous = {"southbound": {"status": "fresh", "net_buy_cny_100m": 12.3}}
        kept = preserve(previous, "southbound", RuntimeError("offline"))
        self.assertEqual(kept["status"], "stale")
        self.assertEqual(kept["net_buy_cny_100m"], 12.3)

    def test_augment_adds_margin_without_private_fields(self):
        flash = {"market": {}, "core_conclusion": "市场。", "sources": {}}
        sentiment = {"generated_at": "x", "metrics": [{"id": "margin_balance", "status": "fresh", "as_of": "2026-08-18", "value": 26000, "total_margin_balance": 26200, "financing_buy_amount": 2000, "change_1d_pct": 1.0, "change_5d_pct": 3.0, "source": "public"}]}
        extras = {"generated_at": "y", "southbound": {"status": "fresh", "net_buy_cny_100m": -10, "as_of": "2026-08-19"}, "index_futures": []}
        out = augment(flash, sentiment, extras)
        self.assertEqual(out["market"]["funding_and_futures"]["margin"]["financing_balance_cny_100m"], 26000)
        self.assertIn("融资余额26000亿元", out["core_conclusion"])
        forbidden = {"quantity", "position_size", "cost_basis", "stop_loss"}
        self.assertFalse(forbidden.intersection(out))


if __name__ == "__main__":
    unittest.main()
