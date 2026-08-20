from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DashboardRenderTests(unittest.TestCase):
    def test_pages_deploys_sentiment_data(self):
        workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text(encoding="utf-8")
        self.assertIn('"Update Watchlist Market Quotes"', workflow)
        self.assertIn("- sentiment.json", workflow)
        self.assertIn("- market.json", workflow)
        self.assertIn("- watchlist.json", workflow)
        self.assertIn("market.json watchlist.json", workflow)
        self.assertNotIn("portfolio.json", workflow)

    def test_pages_deployment_is_verified_after_publish(self):
        workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text(encoding="utf-8")
        deploy_position = workflow.index("uses: actions/deploy-pages@v5")
        verify_position = workflow.index("name: Verify deployed Pages content")
        self.assertGreater(verify_position, deploy_position)
        self.assertIn("scripts/pages_deployment.py build", workflow)
        self.assertIn("scripts/pages_deployment.py verify", workflow)
        self.assertIn("deployment manifest plus index.html", workflow)

    def test_headline_is_not_replaced_by_keywords(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("function newsHeadline(it,titleMap)", html)
        self.assertIn("titleMap?.[it.url]", html)
        self.assertIn("英文原题｜", html)
        self.assertNotIn("(it.keywords_zh||[]).join(' · ')||it.title", html)

    def test_change_radar_requires_real_history(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("function isPulseCandidate(it)", html)
        self.assertIn("points.length>=2", html)
        self.assertIn("Number(it.relevance_score||0)>=5", html)
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

    def test_market_layer_is_loaded_without_portfolio_emphasis(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("fetchJson('market.json','MARKET')", html)
        self.assertNotIn("fetchJson('portfolio.json','PORTFOLIO')", html)
        self.assertNotIn("positionText", html)
        self.assertNotIn("账户持仓", html)

    def test_default_declarations_are_removed(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("系统边界", html)
        self.assertNotIn("AI 信号由 ChatGPT 网页版独立生成", html)
        self.assertNotIn("“共振”需同时满足", html)
        self.assertIn("notice:empty{display:none}", html)

    def test_related_news_requires_material_relevance(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Number(it.relevance_score||0)<5", html)
        self.assertIn("高相关证据", html)


if __name__ == "__main__":
    unittest.main()
