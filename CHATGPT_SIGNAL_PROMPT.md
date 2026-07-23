# ChatGPT 网页版 AI 信号任务

读取本仓库最新的 `data.js`、`watchlist.json` 与当前的 `ai-signals.js`，完成一次 A 股产业信号更新。

## 处理规则

1. 只分析与自选标的存在明确产业链关系、且相较上次生成后新增或显著变化的事件。
2. 合并重复报道，最多保留 12 条信号；宁缺毋滥。
3. 每次必须单独生成 `overseas_markets`，至少覆盖美股、日股、韩股：
   - market / flag / session / updated_at
   - status：positive / negative / mixed / neutral / pending
   - status_label / move / driver
   - a_share_links：对应的 A 股产业链，不超过 4 个
   - validation：当天可观测确认条件
   - sources：最多 3 个可靠来源
   - 优先使用正式收盘或开盘后的最新数据；无法可靠核验时使用 pending，明确写“待验证”，严禁猜测涨跌幅。
   - 日股报价层级：Nikkei Indexes 官方日经225 → JPX 官方 TOPIX（每分钟更新）→ WSJ/FactSet 或 Yahoo Finance 复核。
   - 韩股报价层级：KRX Data Marketplace → WSJ/FactSet 与 Investing.com 交叉复核；韩国财经媒体只用于解释驱动。
   - 开盘表现必须给出：开盘点位、前收、开盘跳空幅度、观测时点及当时涨跌幅。所有时间注明 JST/KST 或北京时间。
   - 至少两个独立报价源的交易日期与开盘价一致，且同一观测时刻的涨跌幅差不超过 0.15 个百分点，才标为已验证；若观测时刻不同，分别展示时间，不能把数值直接当作同刻交叉验证。
   - 若两源冲突，status 使用 pending，status_label 写“来源冲突”，并在 move 中列出冲突值。
   - 美股重点观察纳指、费城半导体、AI服务器/CPO；日股重点观察半导体设备、测试、材料和被动元件；韩股重点观察三星电子、SK海力士、存储/HBM。
4. 每条产业信号必须包含：
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
5. 缺少实时行情时，priced_in 使用 unknown，并把价格、成交量或板块联动写入 validation。
6. 不写入持仓数量、成本、账户资产或无条件买卖指令。
7. 将结果完整写入 `ai-signals.js`，格式为：
   `window.AI_SIGNALS = {generated_at, source_generated_at, generated_by, status, overseas_markets, signals};`
8. generated_at 与 source_generated_at 均使用北京时间；generated_by 固定为 `ChatGPT Web`；status 成功时为 `ready`。
9. 更新后确认 GitHub Pages 部署成功，并在聊天中给出 3–5 条最重要变化及需验证条件。
