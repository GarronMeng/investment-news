# Garron A股信号台

面向个人研究决策的公开产业资讯与信号验证系统：

`产业事件 → A股标的映射 → 量价特征 → 研究决策 → 信号留痕 → 前向验证`

线上入口：<https://garronmeng.github.io/investment-news/>

## 当前能力

- 每个交易日按盘前、午间和收盘检查点自动抓取 100+ 个公开 RSS / Atom 信息源。
- 对 URL 与标题进行规范化去重，保留来源和原文链接。
- GitHub Actions 负责抓取新闻；ChatGPT 网页版负责把产业事件映射到自选 A 股标的，输出方向、强度、作用周期、市场验证条件和失效条件。
- 独立行情任务维护自选标的快照；研究引擎维护最多 140 个交易观察的日线历史，并计算 1/5/20 日收益、均线距离、量能/成交额 Z-score、相对强弱、波动率与回撤。
- `decisions.json` 将新鲜事件信号与确定性量价特征合成透明的研究状态；无新鲜事件时只允许输出 `market_watch`，不伪造基本面信号。
- `signals/YYYY-MM.jsonl` 采用追加式账本保留材料性判断；`signal_evaluation.json` 持续结算 T+1/T+5/T+20、相对基准收益、MFE 与 MAE。
- 独立情绪数据任务通过 OpenBB/YFinance 获取 VIX，并通过 AKShare 对接上交所、深交所两融汇总；失败时保留上次成功值并标记过期。
- Pages 部署前执行 AI 信号新鲜度门槛：源数据超过 36 小时、时间戳缺失或 AI 所引用源与最新 `data.js` 不一致时，旧 AI 信号会被强制降级为 `stale` 并从线上展示数据中清空。
- 不需要模型 API Key；原始新闻、行情/特征、情绪数据与 AI 研判相互独立。

## 个性化范围

当前核心自选池维护在 [`watchlist.json`](watchlist.json)：

- 兆易创新（603986）
- 德明利（001309）
- 中际旭创（300308）
- 东山精密（002384）
- 太极实业（600667）
- 风华高科（000636）
- 国投白银LOF（161226）
- 黄金ETF华安（518880）
- 创新药沪港深ETF天弘（517380）

仓库保持公开，因此不写入持仓数量、成本价、账户资产或私人交易记录。公共 Research Engine 只生成可审计的研究状态；任何私人组合仓位层应与本仓库隔离。

## 自动化闭环

```text
PUBLIC INFORMATION
sources.json → scripts/fetch.py → data.js
                                  │
watchlist.json ────────────────────┤
                                  ↓
                       ChatGPT structured signals
                                  ↓
                            ai-signals.js
                                  │
                                  │ freshness gate
                                  ↓

MARKET RESEARCH
watchlist.json → scripts/fetch_history.py → market_history.json
                                            ↓
                                  scripts/build_features.py
                                            ↓
                                       features.json
                                            │
data.js + ai-signals.js ────────────────────┤
                                            ↓
                                  scripts/build_decisions.py
                                            ↓
                                       decisions.json
                                            ↓
                                signals/YYYY-MM.jsonl
                                            ↓
                                scripts/evaluate_signals.py
                                            ↓
                                signal_evaluation.json
```

### 数据源与失败策略

- A股/ETF/LOF 历史：东方财富 via AKShare 为主，Yahoo Finance chart 为备用。
- 任何失败都不得把旧值伪装成新值；存在可用历史时保留并标记 `stale`，完全无数据时标记不可用。
- 研究引擎的计算规则是显式 heuristic，不宣称机器学习预测能力；真实有效性由后续前向样本逐步验证。

## GitHub Actions

- `Update A-share News`：更新 `data.js` / `history.json`；只受新闻采集相关代码影响，不再被无关行情测试阻断。
- `Update Watchlist Market Quotes`：更新 `market.json`。
- `Update Market Sentiment`：更新 `sentiment.json`。
- `Update Research Engine`：更新历史行情、特征、研究决策、信号账本与前向评价；工作日 08:30 和 15:35（Asia/Shanghai）运行，并在新闻/行情任务成功后重新计算。
- `Deploy dashboard to Pages`：发布前执行 AI freshness gate。

## ChatGPT 信号规则

ChatGPT 网页版按 [`CHATGPT_SIGNAL_PROMPT.md`](CHATGPT_SIGNAL_PROMPT.md) 工作。只有当 `data.js` 足够新鲜，且 `source_generated_at` 与实际读取的 `data.js.generated_at` 完全一致时，`ai-signals.js.status` 才允许为 `ready`。

## 本地验证

```bash
python -m unittest tests/test_fetch.py -v
python -m unittest tests/test_market.py -v
python -m unittest tests/test_research_engine.py -v
python scripts/fetch_history.py
python scripts/build_features.py
python scripts/build_decisions.py
python scripts/update_signal_ledger.py
python scripts/evaluate_signals.py
python server.py
```

浏览器打开 <http://localhost:8793>。

## 系统边界

- 当前研究引擎使用日线历史，盘中价格快照由独立 `market.json` 维护；尚未把分钟级行情纳入历史因子。
- 当前 heuristic 权重尚无足够前向样本支持，不应把 `conviction` 解读为真实概率；其作用是统一、透明地排序证据。
- 当前未接入证券账户或交易接口，不会自动下单。
- 看板处理公开产业信息及自选映射，不构成投资建议。

上游项目：[simonlin1212/investment-news](https://github.com/simonlin1212/investment-news)，MIT License。
