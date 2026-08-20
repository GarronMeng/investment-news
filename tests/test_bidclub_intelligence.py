import importlib.util
import os
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, relative_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fetcher = load_module("fetch_bidclub_intelligence", "scripts/fetch_bidclub_intelligence.py")
augmenter = load_module("augment_daily_flash_bidclub", "scripts/augment_daily_flash_bidclub.py")
BEIJING = timezone(timedelta(hours=8))


class BidClubMappingTests(unittest.TestCase):
    def setUp(self):
        self.watchlist = {
            "assets": [
                {
                    "code": "300308",
                    "name": "中际旭创",
                    "keywords": ["光模块", "CPO", "AI capex", "optical transceiver"],
                    "positive_triggers": ["AI capex"],
                    "negative_triggers": ["AI资本开支下修"],
                },
                {
                    "code": "603986",
                    "name": "兆易创新",
                    "keywords": ["DRAM", "memory", "存储"],
                    "positive_triggers": ["存储价格上行"],
                    "negative_triggers": ["存储价格下行"],
                },
            ]
        }
        self.config = {
            "minimum_relevance_score": 18,
            "max_insights_per_asset": 5,
            "topics": [
                {
                    "id": "ai_compute",
                    "label": "AI算力",
                    "keywords": ["GPU", "AI capex", "inference"],
                    "assets": ["300308"],
                },
                {
                    "id": "memory_hbm",
                    "label": "存储 / HBM",
                    "keywords": ["DRAM", "memory"],
                    "assets": ["603986"],
                },
            ],
        }

    def test_relevant_episode_maps_to_assets_without_trade_instruction(self):
        detail = {
            "slug": "ai-selloff-gavin-baker",
            "show_id": "iltb",
            "title": "The AI Selloff Doesn't Match the Data",
            "published_at": "2026-08-04T12:00:00+00:00",
            "chips": ["person:Gavin Baker"],
            "tldr_md": "GPU rental prices, DRAM and inference usage are accelerating while AI capex remains strong.",
            "digest_md": "The discussion argues compute demand remains strong and memory pricing is firm. AI capex is the key variable to monitor.",
            "source_url": "https://example.com/original",
            "transcript_md": "available",
            "shows": {"name": "Invest Like the Best"},
        }
        now = datetime(2026, 8, 10, 12, 0, tzinfo=BEIJING)
        mapped = fetcher.map_episode(detail, self.watchlist, self.config, now)
        self.assertIsNotNone(mapped)
        codes = {row["code"] for row in mapped["assets"]}
        self.assertEqual(codes, {"300308", "603986"})
        self.assertGreaterEqual(mapped["score"], 18)
        cpo = next(row for row in mapped["assets"] if row["code"] == "300308")
        self.assertEqual(cpo["stance"], "positive_candidate")
        self.assertNotIn("buy", mapped)
        self.assertNotIn("sell", mapped)

    def test_irrelevant_episode_is_dropped(self):
        detail = {
            "slug": "unrelated",
            "title": "A conversation about restaurants",
            "published_at": "2026-08-09T12:00:00+08:00",
            "tldr_md": "A chef discusses menus, hospitality and kitchen design.",
            "digest_md": "No investing or technology content here.",
        }
        now = datetime(2026, 8, 10, 12, 0, tzinfo=BEIJING)
        self.assertIsNone(fetcher.map_episode(detail, self.watchlist, self.config, now))

    def test_asset_overlay_changes_attention_not_directional_composite(self):
        insights = [
            {
                "slug": "x",
                "title": "AI capex update",
                "show": "Example",
                "published_at": "2026-08-10T08:00:00+08:00",
                "bidclub_url": "https://bidclub.ai/e/x",
                "assets": [
                    {
                        "code": "300308",
                        "relevance_score": 80,
                        "stance": "positive_candidate",
                        "positive_trigger_hits": ["AI capex"],
                        "negative_trigger_hits": [],
                    }
                ],
            }
        ]
        overlay = fetcher.build_asset_overlay(insights, self.watchlist, self.config)
        row = overlay["300308"]
        self.assertGreater(row["attention_boost"], 0)
        self.assertNotIn("composite_score", row)
        self.assertNotIn("trade", row)


class DailyFlashAttachTests(unittest.TestCase):
    def test_attach_preserves_existing_flash_and_adds_sidecar(self):
        flash = {"version": 1, "core_conclusion": "keep", "sources": {"market": "t0"}}
        intel = {
            "status": "ok",
            "generated_at": "2026-08-10T09:00:00+08:00",
            "summary": {"episodes_scanned": 20, "relevant_insights": 3, "mapped_assets": 2},
            "insights": [{"slug": "x"}],
            "assets": {"300308": {"attention_boost": 8}},
            "warnings": [],
        }
        result = augmenter.attach(flash, intel)
        self.assertEqual(result["core_conclusion"], "keep")
        self.assertEqual(result["expert_intelligence"]["source"], "BidClub")
        self.assertEqual(result["expert_intelligence"]["asset_attention"]["300308"]["attention_boost"], 8)
        self.assertEqual(result["sources"]["market"], "t0")
        self.assertIn("bidclub_expert_intelligence", result["sources"])


if __name__ == "__main__":
    unittest.main()
