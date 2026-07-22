# Garron A股信号台

面向个人研究决策的公开产业资讯看板：

`产业事件 → A股标的映射 → 影响方向/强度/周期 → 市场验证 → 失效条件`

线上入口：<https://garronmeng.github.io/investment-news/>

## 当前能力

- 工作日北京时间约 08:40 自动抓取 100+ 个公开 RSS / Atom 信息源。
- 对 URL 与标题进行规范化去重，保留来源和原文链接。
- GitHub Actions 负责抓取新闻；ChatGPT 网页版负责把产业事件映射到自选 A 股标的，输出方向、强度、作用周期、市场验证条件和失效条件。
- 不需要模型 API Key；原始新闻更新与 AI 研判相互独立。
- 通过 GitHub Pages 发布响应式网页，手机与电脑均可访问。

## 个性化范围

当前核心自选池维护在 [`watchlist.json`](watchlist.json)：

- 兆易创新（603986）
- 德明利（001309）
- 中际旭创（300308）
- 东山精密（002384）
- 太极实业（600667）
- 风华高科（000636）

仓库保持公开，因此不写入持仓数量、成本价、账户资产或交易记录。

## 一次性部署设置

1. 打开仓库 `Settings → Pages`，将 Source 设为 `GitHub Actions`。
2. 打开 `Actions → Update A-share Signals → Run workflow`，手动验证一次新闻抓取。
3. ChatGPT 网页版按 [`CHATGPT_SIGNAL_PROMPT.md`](CHATGPT_SIGNAL_PROMPT.md) 读取最新数据，并将结构化研判写入 [`ai-signals.js`](ai-signals.js)。

无需在公开仓库配置模型 API Key。

## 自动化闭环

```text
sources.json
  ↓ scripts/fetch.py：抓取、时效过滤、去重、自选关键词命中
data.js ───────────────┐
                       ↓ ChatGPT 网页版：结构化产业信号
watchlist.json ────────┘
                       ↓ ai-signals.js
data.js + ai-signals.js
  ↓ deploy-pages.yml
GitHub Pages
```

`Update A-share Signals` 支持定时和手动运行，只更新 `data.js`。ChatGPT 网页版独立更新 `ai-signals.js`；两类更新都会触发 Pages 部署，且互不覆盖。

## 本地验证

```bash
python scripts/fetch.py
python server.py
```

浏览器打开 <http://localhost:8793>。## 系统边界

- 当前未接入实时行情，`priced_in` 通常为 `unknown`，需要结合价格、成交量和板块联动验证。
- 当前未接入证券账户或交易接口，不会自动下单。
- 看板处理公开产业信息及自选映射，不构成投资建议。

上游项目：[simonlin1212/investment-news](https://github.com/simonlin1212/investment-news)，MIT License。
