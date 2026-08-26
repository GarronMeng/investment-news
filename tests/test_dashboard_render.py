from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DashboardRenderTests(unittest.TestCase):
    def test_decision_cockpit_has_action_first_hierarchy(self):
        html = (ROOT / "dashboard-v5.html").read_text(encoding="utf-8")
        ordered_sections = [
            'id="actions"',
            'id="portfolioSection"',
            'id="themesSection"',
            'id="catalystsSection"',
            'id="marketDetail"',
            'id="dataHealth"',
        ]
        positions = [html.index(section) for section in ordered_sections]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("风险优先", html)
        self.assertIn("等待确认", html)
        self.assertIn("可观察", html)
        self.assertIn('aria-expanded="false"', html)

    def test_decision_cockpit_encodes_recent_execution_discipline(self):
        html = (ROOT / "dashboard-v5.html").read_text(encoding="utf-8")
        for text in (
            "09:25 · 竞价定方向",
            "09:35 · 第一次分歧",
            "10:00 · 资金选择",
            "14:00 · 承接 / 兑现",
            "等第一次回踩",
            "默认放弃追价",
            "仅新重大催化复核",
        ):
            self.assertIn(text, html)
        self.assertIn("function openingGap(q)", html)
        self.assertIn("gap>=6", html)
        self.assertIn("gap>=4", html)
        self.assertIn("gap>=2", html)
        self.assertIn("偏多情景", html)
        self.assertIn("基准情景", html)
        self.assertIn("偏空情景", html)

    def test_decision_cockpit_separates_logic_price_and_private_holdings(self):
        html = (ROOT / "dashboard-v5.html").read_text(encoding="utf-8")
        self.assertIn("逻辑获支持", html)
        self.assertIn("价格未确认", html)
        self.assertIn("下一确认", html)
        self.assertIn("失效条件", html)
        self.assertIn("garron-private-portfolio-v1", html)
        self.assertIn("localStorage.getItem(PORTFOLIO_KEY)", html)
        self.assertNotIn("fetchJson('portfolio.json'", html)

    def test_decision_cockpit_surfaces_data_lag_and_quote_confidence(self):
        html = (ROOT / "dashboard-v5.html").read_text(encoding="utf-8")
        self.assertIn("q.confidence!=='low'", html)
        self.assertIn("低置信度报价不参与确认", html)
        self.assertIn("技术层截至", html)
        self.assertIn("等行情刷新，不沿用旧价", html)

    def test_legacy_daily_flash_extensions_skip_decision_cockpit(self):
        html = (ROOT / "dashboard-v5.html").read_text(encoding="utf-8")
        extras = (ROOT / "daily-flash-extras.js").read_text(encoding="utf-8")
        intelligence = (ROOT / "daily-flash-intelligence.js").read_text(encoding="utf-8")
        marker = 'meta[name="dashboard-mode"][content="decision-cockpit"]'
        self.assertIn('<meta name="dashboard-mode" content="decision-cockpit">', html)
        self.assertIn(marker, extras)
        self.assertIn(marker, intelligence)

    def test_pages_keeps_decision_cockpit_as_root_and_detail_pages_as_drilldowns(self):
        workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text(encoding="utf-8")
        self.assertIn("cp dashboard-v5.html public/index.html", workflow)
        self.assertIn("cp dashboard-v3.html public/dashboard-v3.html", workflow)
        self.assertIn("cp dashboard-v4.html public/dashboard-v4.html", workflow)

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
