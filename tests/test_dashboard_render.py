from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DashboardRenderTests(unittest.TestCase):
    def test_pages_deploys_sentiment_data(self):
        workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text(encoding="utf-8")
        self.assertIn('workflows: ["Update A-share News", "Update Market Sentiment"]', workflow)
        self.assertIn("- sentiment.json", workflow)
        self.assertIn("cp index.html data.js ai-signals.js sentiment.json .nojekyll public/", workflow)

    def test_headline_is_not_replaced_by_keywords(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("function newsHeadline(it){return it.zh||it.title||'未命名新闻'}", html)
        self.assertNotIn("(it.keywords_zh||[]).join(' · ')||it.title", html)

    def test_change_radar_requires_real_history(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("function isPulseCandidate(it)", html)
        self.assertIn("points.length>=2", html)
        self.assertIn("filter(isPulseCandidate)", html)

    def test_print_layout_avoids_split_cards(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("@media print", html)
        self.assertIn("page-break-inside:avoid", html)


if __name__ == "__main__":
    unittest.main()
