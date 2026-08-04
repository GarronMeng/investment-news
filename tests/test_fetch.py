import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from fetch import (
    contains_pattern,
    enrich_items,
    merge_event_clusters,
    update_history,
)


class SignalHistoryTests(unittest.TestCase):
    def sample_industries(self):
        return [{
            "key": "ai",
            "name": "AI / 大模型",
            "items": [
                {
                    "id": "en-story",
                    "title": "OpenAI launches an artificial intelligence agent",
                    "summary": "A new product launch for enterprise users",
                    "source": "OpenAI",
                    "language": "en",
                    "agenda_layer": "primary",
                    "url": "https://example.com/en",
                    "ts": 200,
                },
                {
                    "id": "zh-story",
                    "title": "OpenAI 发布人工智能智能体",
                    "summary": "面向企业用户推出新产品",
                    "source": "量子位",
                    "language": "zh",
                    "agenda_layer": "media",
                    "url": "https://example.com/zh",
                    "ts": 100,
                },
            ],
        }]

    def test_short_keyword_uses_word_boundary(self):
        self.assertTrue(contains_pattern("dram prices rise", "dram"))
        self.assertFalse(contains_pattern("a dramatic move", "dram"))

    def test_cross_language_event_is_merged_and_resonance_needs_time(self):
        industries = self.sample_industries()
        enrich_items(industries, {"assets": []})
        merge_event_clusters(industries)
        self.assertEqual(len(industries[0]["items"]), 1)
        item = industries[0]["items"][0]
        self.assertEqual(item["cluster_size"], 2)
        self.assertEqual(item["languages"], ["en", "zh"])

        history = update_history(industries, {"version": 1, "topics": {}}, now_ts=1_000_000)
        self.assertFalse(item["resonance"]["confirmed"])
        update_history(industries, history, now_ts=1_000_000 + 7 * 3600)
        self.assertTrue(item["resonance"]["confirmed"])


if __name__ == "__main__":
    unittest.main()

