// 由 ChatGPT 网页版生成；新闻抓取工作流不会覆盖本文件。
window.AI_SIGNALS = {
  "generated_at": "2026-08-03 09:12",
  "source_generated_at": "2026-08-02 17:24",
  "generated_by": "ChatGPT Web",
  "status": "ready",
  "overseas_markets": [
    {
      "market": "美股",
      "flag": "🇺🇸",
      "session": "7月31日收盘（周一盘前最新正式行情）",
      "updated_at": "2026-08-03 09:12 CST",
      "status": "positive",
      "status_label": "AI需求支撑延续，长端利率仍限制估值",
      "move": "标普500 +0.70%｜道指 +0.53%｜纳指 +1.00%",
      "driver": "Amazon因AWS增长加速和上调AI资本开支而大涨，延续Microsoft财报后的AI基础设施修复；Apple因收入指引和零部件约束下跌，显示消费电子内部仍分化。美国10年期国债收益率周五一度升至4.747%，高估值成长仍受利率约束。周末无新的美股正式交易价格。",
      "a_share_links": ["CPO", "PCB", "存储芯片", "消费电子"],
      "validation": "A股开盘后观察中际旭创、东山精密能否获得海外云资本开支承接；若继续冲高回落，则需求利好尚未转化为稳定价格趋势。",
      "sources": [
        "https://www.reuters.com/business/nasdaq-100-leads-us-futures-higher-amazon-surge-offsets-apple-decline-2026-07-31/",
        "https://www.reuters.com/world/china/global-markets-global-markets-2026-07-31/"
      ]
    },
    {
      "market": "日股",
      "flag": "🇯🇵",
      "session": "8月3日早盘",
      "updated_at": "2026-08-03 09:12 CST",
      "status": "negative",
      "status_label": "周五急涨后回吐，电子与汽车领跌",
      "move": "开盘63,834.95（较前收低0.82%）｜09:36 JST报63,153.62，跌1.88%",
      "driver": "日经225前收64,362.02，今早低开后继续走弱；村田制作所等电子权重领跌。美元兑日元由周五东京收盘附近160.33降至157.62，日元走强削弱出口股估值，同时中东局势仍令风险偏好反复。",
      "a_share_links": ["被动元件", "消费电子", "半导体设备", "AI硬件"],
      "validation": "观察日经能否收复开盘价，以及风华高科、东山精密是否能够摆脱日股电子链回撤形成独立承接。",
      "sources": [
        "https://www.wsj.com/market-data/quotes/index/JP/NIK/historical-prices",
        "https://www.wsj.com/finance/stocks/nikkei-falls-1-4-dragged-by-electronics-auto-stocks-e85119b4",
        "https://indexes.nikkei.co.jp/en/nkave/index/profile"
      ]
    },
    {
      "market": "韩股",
      "flag": "🇰🇷",
      "session": "8月3日早盘",
      "updated_at": "2026-08-03 09:12 CST",
      "status": "negative",
      "status_label": "出口利好未抵消周五暴涨后的回吐",
      "move": "开盘6,358.27（较前收低3.60%）｜09:41 KST报6,298.12，跌4.51%",
      "driver": "KOSPI前收6,595.45，今早显著低开；韩国7月半导体和计算机出口数据继续验证AI与存储需求，但周五17.91%的创纪录反弹计价过快，短线资金兑现和高波动风险重新主导。",
      "a_share_links": ["存储芯片", "HBM", "封测", "AI服务器"],
      "validation": "观察KOSPI能否守住早盘低点并缩窄跌幅；A股对应关注兆易创新、德明利、太极实业能否避免跟随高开低走。",
      "sources": [
        "https://www.wsj.com/market-data/quotes/index/KR/SEU/historical-prices",
        "https://www.reuters.com/world/asia-pacific/south-korea-july-exports-beat-forecasts-robust-demand-ai-investments-2026-08-01/",
        "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=en"
      ]
    }
  ],
  "signals": [
    {
      "event": "兆易创新10亿至20亿元回购注销方案进入股东会审议与价格验证阶段",
      "industry": "company",
      "industry_name": "公司资本运作 / 存储芯片",
      "direction": "positive",
      "strength": 5,
      "horizon": "1-4w",
      "priced_in": "medium",
      "reason": "公司董事会已通过以集中竞价方式回购A股的方案，金额不低于10亿元、不超过20亿元，回购股份全部用于注销并减少注册资本；公司8月3日进一步发布临时股东会通知。该安排有助于减少股本并传递信心，但仍需股东会审议，实际成交时间、均价和最终规模尚未确定；长鑫上市后的资金替代仍是独立约束。",
      "assets": ["603986"],
      "validation": [
        "股东会通过方案后公司启动回购，并持续披露实际成交金额和价格",
        "公告后股价相对存储板块转强，且收盘未出现明显高开低走"
      ],
      "invalidation": [
        "股东会未通过、方案延期或实际实施长期低于方案下限预期",
        "股价放量跌破7月31日低点，显示市场继续交易长鑫资金替代与筹码压力"
      ],
      "urls": [
        "https://big5.sse.com.cn/disclosure/listedinfo/announcement/c/new/2026-08-01/603986_20260801_NYOY.pdf",
        "https://data.eastmoney.com/notices/stock/603986.html"
      ]
    },
    {
      "event": "韩国半导体出口强劲但KOSPI周一低开逾3%，存储利好进入高波动价格验证",
      "industry": "semi",
      "industry_name": "存储芯片 / AI硬件",
      "direction": "mixed",
      "strength": 5,
      "horizon": "1-5d",
      "priced_in": "high",
      "reason": "韩国7月半导体出口增长179%、计算机出口增长404%，继续确认AI和存储需求；但KOSPI继周五上涨17.91%后，8月3日以6,358.27点低开，较前收低3.60%，09:41 KST跌4.51%。基本面利好与筹码兑现同时存在，不能仅以出口数据推导A股存储、封测和AI硬件单向上涨。",
      "assets": ["603986", "001309", "600667", "300308", "002384"],
      "validation": [
        "KOSPI、三星和SK海力士守住早盘低点并缩窄跌幅，A股相关板块同步获得承接",
        "后续存储价格、出货量或供应链订单继续确认增长并非仅由价格基数驱动"
      ],
      "invalidation": [
        "韩股继续扩大跌幅并回吐周五反弹主要成果",
        "A股相关标的高开低走并跌破7月31日低点，显示利好已被过度计价"
      ],
      "urls": [
        "https://www.reuters.com/world/asia-pacific/south-korea-july-exports-beat-forecasts-robust-demand-ai-investments-2026-08-01/",
        "https://www.wsj.com/market-data/quotes/index/KR/SEU/historical-prices"
      ]
    },
    {
      "event": "MLCC涨价进入执行期，但日股电子链早盘回落提高短线验证门槛",
      "industry": "components",
      "industry_name": "被动元件 / MLCC",
      "direction": "mixed",
      "strength": 4,
      "horizon": "1-4w",
      "priced_in": "medium",
      "reason": "三星电机自8月1日起上调MLCC出货价格、太阳诱电计划9月调价，产业涨价进入执行阶段；与此同时，8月3日日经低开后继续走弱，村田制作所早盘跌约5%，说明海外被动元件和电子链的短线风险偏好并未同步改善。风华高科此前已显著上涨，后续需由渠道成交价、订单和下游接受度验证盈利弹性。",
      "assets": ["000636"],
      "validation": [
        "渠道报价、订单显示高容值和高可靠MLCC价格与需求同步改善",
        "风华高科相对被动元件指数保持强势，且高换手逐步下降"
      ],
      "invalidation": [
        "下游抵制涨价或削减订单，实际成交价未跟随通知",
        "风华高科跌破催化前区间，且日韩电子权重继续显著回撤"
      ],
      "urls": [
        "https://www.cls.cn/detail/2441445",
        "https://www.wsj.com/finance/stocks/nikkei-falls-1-4-dragged-by-electronics-auto-stocks-e85119b4"
      ]
    }
  ]
};
