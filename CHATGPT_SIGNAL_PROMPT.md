# ChatGPT 网页版 AI 信号任务

读取本仓库最新的 `data.js`、`watchlist.json` 与当前的 `ai-signals.js`，完成一次 A 股产业信号更新。

## 处理规则

1. 只分析与自选标的存在明确产业链关系、且相较上次生成后新增或显著变化的事件。
2. 合并重复报道，最多保留 12 条信号；宁缺毋滥。
3. 每条信号必须包含：
   - event：事件概括
   - industry / industry_name
   - direction：positive / negative / mixed / neutral
   - strength：1–5
   - horizon：intraday / 1-5d / 1-4w / 1-3m
   - priced_in：unknown / low / medium / high
   - reason
   - assets：仅使用 watchlist.json 中的代码
   - validation：最多 2 条可观测验证条件
   - invalidation：最多 2 条失效条件
   - urls：最多 3 个新闻证据链接
4. 缺少实时行情时，priced_in 使用 unknown，并把价格、成交量或板块联动写入 validation。
5. 不写入持仓数量、成本、账户资产或无条件买卖指令。
6. 将结果完整写入 `ai-signals.js`，格式为：
   `window.AI_SIGNALS = {generated_at, source_generated_at, generated_by, status, signals};`
7. generated_at 与 source_generated_at 均使用北京时间；generated_by 固定为 `ChatGPT Web`；status 成功时为 `ready`。
8. 更新后确认 GitHub Pages 部署成功，并在聊天中给出 3–5 条最重要变化及需验证条件。
