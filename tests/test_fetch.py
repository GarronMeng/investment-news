import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from fetch import (
    contains_pattern,
    enrich_items,
    history_progress,
    is_trajectory_signal,
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

    def test_snapshot_is_not_reported_as_change(self):
        item = {
            "trajectory": {"label": "new", "points": [1]},
            "resonance": {"source_count": 1, "confirmed": False},
            "relevance_score": 10,
        }
        self.assertFalse(is_trajectory_signal(item))
        item["trajectory"] = {"label": "surge", "points": [12, 1]}
        self.assertTrue(is_trajectory_signal(item))
        item["relevance_score"] = 4
        self.assertFalse(is_trajectory_signal(item))
        item["resonance"]["confirmed"] = True
        self.assertTrue(is_trajectory_signal(item))

    def test_history_progress_exposes_sampling_state(self):
        history = {
            "updated_at": "2026-08-04 11:50",
            "topics": {
                "a": {"points": [{"ts": 100}, {"ts": 3700}]},
                "b": {"points": [{"ts": 3700}]},
            },
        }
        progress = history_progress(history)
        self.assertEqual(progress["sampling_windows"], 2)
        self.assertEqual(progress["comparable_topics"], 1)
        self.assertEqual(progress["coalesce_minutes"], 30)


if __name__ == "__main__":
    unittest.main()
