# Garron 投资工作台

面向个人研究决策的公开产业资讯、市场状态与信号验证系统：

`产业事件 → A股标的映射 → 市场/技术/估值校准 → 研究决策 → 信号留痕 → 前向验证`

线上入口：<https://garronmeng.github.io/investment-news/>

附属页面：

- 多周期 K 线：`/chart.html`
- 私人组合层：`/portfolio.html`（仅浏览器本地存储）
- Research：`/research.html`
- 经典版：`/classic.html`
- V2 备份：`/v2.html`

## 当前能力

### 1. 产业事件与 AI 研判

- 每个交易日按盘前、午间和收盘检查点自动抓取 100+ 个公开 RSS / Atom 信息源。
- 对 URL 与标题进行规范化去重，保留来源和原文链接。
- GitHub Actions 负责抓取新闻；ChatGPT 网页版负责把产业事件映射到自选 A 股标的，输出方向、强度、作用周期、市场验证条件和失效条件。
- `decisions.json` 将新鲜事件信号与确定性市场证据合成透明的研究状态；无新鲜事件时只允许输出 `market_watch`，不伪造基本面信号。

### 2. Market State Engine

- `market_state.json` 维护全 A 市场广度、核心 A/H 指数、涨跌停结构、成交额、行业强弱、行业资金与 ETF 成交活跃度代理。
- 全 A 广度以东方财富为主源，失败时单次回退新浪财经；旧数据不会伪装为实时数据。
- 行业涨跌与行业资金以东方财富为主源；失败时尝试同花顺独立行业资金流接口。
- 市场状态分为 `Risk-on / Narrow Risk-on / Transition / Risk-off`。当前显式 heuristic 为：市场广度 55% + 核心指数 30% + 涨跌停结构 15%。该状态不是收益概率。
- ETF 模块明确标记为“成交额活跃度代理”，不把成交额冒充净申购或资金净流入。

### 3. 技术条件矩阵

- 研究引擎维护最多 140 个交易日的公开行情历史。
- `features.json` 计算 1/5/20 日收益、MA20/MA60 距离、量能/成交额 Z-score、相对强弱、波动率与回撤。
- `technical.json` 计算 MA60 位置/方向、RSI(14)、MACD 状态与交叉持续时间、20 日量能比和 20 日突破/新低状态。
- 技术条件只描述成立程度和状态变化，不生成无条件买卖或仓位指令。
- `chart.html` 提供 20D / 60D / 140D 日线 OHLCV K 线与 MA20 / MA60 可视化。

### 4. 指数估值

- `valuation.json` 通过 AKShare 对接中证指数历史行情中的真实“滚动市盈率”。
- 当前覆盖：沪深300、中证500、中证1000、中证800。
- 同一滚动 PE 序列内计算 3 年、5 年和 10 年历史分位，并保留 10 年月度轨迹。
- 不用价格分位代替 PE 分位；取不到真实估值时显示 `stale/unavailable`。
- 当前只有沪深300十年 PE 分位进入总风险温度，其余估值仅用于观察，避免重复计分。

### 5. Garron Market Risk Temperature

- `risk_score.json` 输出 0–100 的市场风险温度；分数越高表示估值/结构/趋势/情绪环境更脆弱或压力更高，不代表下跌概率。
- 当前权重：估值 20% + 市场结构 25% + 基准趋势 20% + 两融 15% + 海外风险 10% + 集中度 10%。
- 缺失组件直接剔除并按剩余可用权重重新归一，同时显示 `coverage`；不会为凑满 100 分补造数据。
- 风险温度只做环境校准，不生成买卖、止损或仓位指令。

### 6. 情绪、信号留痕与前向验证

- 独立情绪任务通过 OpenBB/YFinance 获取 VIX，并通过 AKShare 对接上交所、深交所两融汇总；失败时保留上次成功值并标记过期。
- `signals/YYYY-MM.jsonl` 采用追加式账本保留材料性判断。
- `signal_evaluation.json` 持续结算 T+1/T+5/T+20、相对基准收益、MFE 与 MAE。
- 样本不足时，页面明确不把短期胜率解读为稳定概率。

### 7. 数据新鲜度与部署安全

- Pages 部署前执行 AI 信号新鲜度门槛：源数据超过 36 小时、时间戳缺失或 AI 所引用源与最新 `data.js` 不一致时，旧 AI 信号会被强制降级为 `stale` 并从线上展示数据中清空。
- 原始新闻、行情/特征、市场状态、估值、情绪与 AI 研判保持独立数据层。
- 不需要模型 API Key。

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

仓库保持公开，因此 GitHub 数据文件、提交历史和 Actions **不得写入持仓数量、成本价、账户资产或私人交易记录**。

`portfolio.html` 是唯一的私人组合层：数量、成本、手动现价和分组仅保存在用户当前浏览器的 `localStorage`。页面代码是公开的，但私人数据不会随页面一起发布，也不会被发送回 GitHub。清理浏览器数据会删除这些本地记录；跨设备使用应由用户自行导出/导入 JSON。

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

MARKET STATE
public quote sources → scripts/fetch_market.py → market.json
public market sources → scripts/fetch_market_state.py → market_state.json
                                                     │
                                                     ↓
                                              regime / breadth

MARKET RESEARCH
watchlist.json → scripts/fetch_history.py → market_history.json
                                            ├→ scripts/build_features.py  → features.json
                                            └→ scripts/build_technical.py → technical.json

VALUATION / RISK
CSI index history → scripts/fetch_valuation.py → valuation.json
market_state + technical + valuation + sentiment
                    ↓
          scripts/build_risk_score.py
                    ↓
              risk_score.json

DECISION / EVALUATION
data.js + ai-signals.js + features.json
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

## 数据源与失败策略

- A股/ETF/LOF 历史：东方财富 / 新浪财经 via AKShare，并保留独立备用路径。
- 自选行情：东方财富 via AKShare 为主，Yahoo Finance chart 为逐标的备用。
- 核心指数快照：腾讯行情。
- 指数估值：中证指数历史行情 via AKShare，使用滚动市盈率。
- VIX：OpenBB/YFinance，必要时使用 CBOE 官方历史数据。
- 两融：上交所 + 深交所官方汇总 via AKShare。
- 任何失败都不得把旧值伪装成新值；存在可用历史时保留并标记 `stale`，完全无数据时标记 `unavailable`。
- 研究与风险引擎均使用显式 heuristic，不宣称机器学习预测能力；真实有效性由后续前向样本持续验证。

## GitHub Actions

- `Update A-share News`：更新 `data.js` / `history.json`。
- `Update Watchlist Market Quotes`：更新 `market.json` 与 `market_state.json`。
- `Update Market Sentiment`：更新 `sentiment.json`。
- `Update Research Engine`：更新历史行情、技术矩阵、估值、风险温度、研究决策、信号账本与前向评价；工作日 08:30 和 15:35（Asia/Shanghai）运行，并在新闻/行情/情绪任务成功后重新计算。
- `Deploy dashboard to Pages`：发布 V3 工作台、K 线、Research 与浏览器本地私人组合层，并在发布前执行 AI freshness gate 与公共产物契约检查。

## ChatGPT 信号规则

ChatGPT 网页版按 [`CHATGPT_SIGNAL_PROMPT.md`](CHATGPT_SIGNAL_PROMPT.md) 工作。只有当 `data.js` 足够新鲜，且 `source_generated_at` 与实际读取的 `data.js.generated_at` 完全一致时，`ai-signals.js.status` 才允许为 `ready`。

## 本地验证

```bash
python -m unittest tests/test_fetch.py -v
python -m unittest tests/test_market.py -v
python -m unittest tests/test_market_state.py -v
python -m unittest tests/test_research_engine.py -v
python -m unittest tests/test_technical.py -v
python -m unittest tests/test_valuation.py -v
python -m unittest tests/test_risk_score.py -v
python scripts/fetch_history.py
python scripts/build_features.py
python scripts/build_technical.py
python scripts/fetch_valuation.py
python scripts/build_risk_score.py
python scripts/build_decisions.py
python scripts/update_signal_ledger.py
python scripts/evaluate_signals.py
python server.py
```

浏览器打开 <http://localhost:8793>。

## 系统边界

- 当前研究历史仍为日线，盘中价格快照由独立 `market.json` / `market_state.json` 维护；尚未把分钟级行情纳入历史因子。
- 当前 heuristic 权重尚无足够前向样本支持，不应把 `conviction`、`regime score` 或 `risk score` 解读为真实概率。
- 当前未接入证券账户或交易接口，不会自动下单。
- 公共看板处理公开产业信息及自选映射，不构成投资建议。

上游项目：[simonlin1212/investment-news](https://github.com/simonlin1212/investment-news)，MIT License。
