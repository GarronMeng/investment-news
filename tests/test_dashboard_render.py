from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DashboardRenderTests(unittest.TestCase):
    def test_pages_deploys_sentiment_data(self):
        workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text(encoding="utf-8")
        self.assertIn('"Update Watchlist Market Quotes"', workflow)
        self.assertIn("- sentiment.json", workflow)
        self.assertIn("- market.json", workflow)
        self.assertIn("- portfolio.json", workflow)
        self.assertIn("- watchlist.json", workflow)
        self.assertIn("market.json portfolio.json watchlist.json", workflow)

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
        self.assertIn("beforeprint", html)
        self.assertIn("details:not([open])", html)

    def test_decision_fields_are_visible_without_expanding(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("下一验证", html)
        self.assertIn("失效条件", html)
        self.assertIn("定价状态", html)
        self.assertNotIn("已交易 ${esc(uiLabel('priced'", html)

    def test_market_and_portfolio_layers_are_loaded(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("fetchJson('market.json','MARKET')", html)
        self.assertIn("fetchJson('portfolio.json','PORTFOLIO')", html)
        self.assertIn("账户未同步 · 持仓/成本未配置", html)

    def test_related_news_requires_material_relevance(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Number(it.relevance_score||0)<5", html)
        self.assertIn("高相关证据", html)


if __name__ == "__main__":
    unittest.main()
