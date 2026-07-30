// 由 ChatGPT 网页版生成；新闻抓取工作流不会覆盖本文件。
window.AI_SIGNALS = {
  "generated_at": "2026-07-30 09:09",
  "source_generated_at": "2026-07-30 08:55",
  "generated_by": "ChatGPT Web",
  "status": "ready",
  "overseas_markets": [
    {
      "market": "美股",
      "flag": "🇺🇸",
      "session": "7月29日收盘",
      "updated_at": "2026-07-30 09:09 CST",
      "status": "negative",
      "status_label": "美联储偏鹰、大盘与科技同步下跌",
      "move": "标普500 -1.52%｜道指 -2.19%｜纳指 -1.74%｜纳斯达克100 -2.1%",
      "driver": "美联储将利率维持在3.50%-3.75%，但12名决策者中有3人主张加息25个基点；油价因中东冲突反弹，重新抬升通胀与估值压力。微软云业务超预期与Meta自由现金流骤降形成AI投资回报分化。",
      "a_share_links": [
        "CPO",
        "PCB",
        "存储芯片",
        "成长估值"
      ],
      "validation": "A股开盘后观察中际旭创、东山精密能否因微软云业务超预期而相对科技指数抗跌；同时跟踪美债收益率、原油和美元是否继续上行。",
      "sources": [
        "https://www.reuters.com/business/sp-500-nasdaq-futures-inch-up-before-fed-decision-chip-stocks-wobble-2026-07-29/",
        "https://www.reuters.com/business/meta-narrows-annual-capex-forecast-ai-buildout-grows-2026-07-29/",
        "https://apnews.com/article/f7dff4fb9d51a2bdec56a13e5da1053d"
      ]
    },
    {
      "market": "日股",
      "flag": "🇯🇵",
      "session": "7月30日早盘",
      "updated_at": "2026-07-30 09:54 JST",
      "status": "mixed",
      "status_label": "低开后快速反弹",
      "move": "开盘61,258.34，前收61,434.19，跳空 -0.29%；09:54报62,093.07（+1.07%）",
      "driver": "日经低开后转涨，说明美股下跌并未形成单向传导；日经官方与WSJ对交易日期、开盘和前收一致，WSJ在09:34报62,224.28（+1.29%），观测时刻不同分别保留。",
      "a_share_links": [
        "半导体设备",
        "存储芯片",
        "被动元件",
        "电子材料"
      ],
      "validation": "观察日经能否守住前收和早盘低点，以及东京电子、Advantest与铠侠是否同步修复；A股关注太极实业、风华高科相对行业指数的承接。",
      "sources": [
        "https://indexes.nikkei.co.jp/en/nkave/index/profile",
        "https://www.wsj.com/market-data/quotes/index/JP/NIK/historical-prices",
        "https://www.jpx.co.jp/english/markets/indices/realvalues/01.html"
      ]
    },
    {
      "market": "韩股",
      "flag": "🇰🇷",
      "session": "7月30日早盘",
      "updated_at": "2026-07-30 09:13 KST",
      "status": "mixed",
      "status_label": "小幅高开、去杠杆压力仍在",
      "move": "开盘5,681.77，前收5,663.24，跳空 +0.33%；09:13报5,677.70（+0.26%）",
      "driver": "三星电子二季度经营利润创纪录、AI服务器存储需求强劲，为存储基本面提供支撑；但KOSPI此前连续大跌，SK海力士业绩未达到高预期，早盘仅小幅高开，尚未确认风险反转。KRX为官方基准，WSJ与Investing.com复核开盘和前收；后续报价因时点不同不作同刻比较。",
      "a_share_links": [
        "存储芯片",
        "HBM",
        "封测",
        "AI服务器"
      ],
      "validation": "观察KOSPI能否守住前收、三星电子与SK海力士是否同步走强；A股关注兆易创新、德明利、太极实业能否摆脱前期弱势。",
      "sources": [
        "https://data.krx.co.kr/",
        "https://www.wsj.com/market-data/quotes/index/KR/SEU/historical-prices",
        "https://www.reuters.com/world/asia-pacific/samsung-q2-profit-jumps-19-fold-ai-chip-demand-offsets-mobile-loss-2026-07-30/"
      ]
    }
  ],
  "signals": [
    {
      "event": "美联储按兵不动但出现三票加息异议，油价反弹重新抬升成长估值压力",
      "industry": "macro",
      "industry_name": "利率 / 跨资产",
      "direction": "negative",
      "strength": 5,
      "horizon": "1-5d",
      "priced_in": "medium",
      "reason": "美联储将政策利率维持在3.50%-3.75%，避免了即时加息冲击，但12名决策者中有3人主张加息25个基点，鹰派程度高于常态。标普、纳指和道指同步大跌，布伦特原油因中东冲突反弹约7%，通胀、实际利率与风险偏好三条通道重新约束高估值科技。黄金、白银受避险和利率预期变化支撑，但人民币汇率与国内基金溢价会改变A股产品映射。",
      "assets": [
        "300308",
        "002384",
        "603986",
        "001309",
        "600667",
        "000636"
      ],
      "validation": [
        "美债收益率、美元与原油不再同步上行，A股成长指数开盘后相对大盘企稳",
        "黄金、白银上涨能得到人民币计价ETF净值确认，而非仅体现二级市场溢价"
      ],
      "invalidation": [
        "油价继续急升并推动市场重新显著上调9月加息概率",
        "海外科技继续放量下跌并带动A股半导体、CPO和PCB出现新一轮批量跌停"
      ],
      "urls": [
        "https://www.reuters.com/business/sp-500-nasdaq-futures-inch-up-before-fed-decision-chip-stocks-wobble-2026-07-29/",
        "https://www.reuters.com/world/asia-pacific/gold-edges-lower-ahead-fed-decision-interest-rates-2026-07-29/"
      ]
    },
    {
      "event": "微软云业务验证AI需求，Meta现金流骤降令资本开支质量成为新分水岭",
      "industry": "ai",
      "industry_name": "AI基础设施",
      "direction": "mixed",
      "strength": 5,
      "horizon": "1-5d",
      "priced_in": "low",
      "reason": "微软季度收入约900亿美元，Azure增长43%，云收入增长27%，并维持高强度数据中心投入，直接支持高速光模块和服务器PCB需求；Meta收入增长28%，但自由现金流同比下降约91%至7.84亿美元，资本开支区间收窄至1300亿-1450亿美元后股价盘后大跌。市场不再只交易资本开支总量，而是区分云收入兑现、现金流和投资回报。",
      "assets": [
        "300308",
        "002384"
      ],
      "validation": [
        "中际旭创、东山精密相对CPO与PCB指数抗跌，微软财报的需求验证强于Meta现金流担忧",
        "后续云厂商继续确认1.6T光模块、AI服务器和数据中心建设节奏"
      ],
      "invalidation": [
        "更多云厂商出现现金流恶化并下修资本开支或延迟数据中心项目",
        "微软盘后涨幅显著回吐，AI硬件股继续无差别下跌"
      ],
      "urls": [
        "https://apnews.com/article/f7dff4fb9d51a2bdec56a13e5da1053d",
        "https://www.reuters.com/business/meta-narrows-annual-capex-forecast-ai-buildout-grows-2026-07-29/"
      ]
    },
    {
      "event": "中际旭创H股今日上市，巨额募资与暗盘小幅破发共同开启A/H定价验证",
      "industry": "ai",
      "industry_name": "CPO / 光模块",
      "direction": "mixed",
      "strength": 5,
      "horizon": "intraday",
      "priced_in": "medium",
      "reason": "中际旭创H股以980港元发行，基础发行5450万股，募资约534.1亿港元；暗盘收于971港元，较发行价低0.92%。上市融资有利于全球产能、研发和客户拓展，但新增流通供给、A/H估值比较及暗盘破发会影响首日风险偏好。公司同时收到40亿至80亿元A股回购提议，构成价格支撑变量，但正式方案和执行节奏仍需确认。",
      "assets": [
        "300308"
      ],
      "validation": [
        "H股开盘后收复980港元发行价且成交有序，A股相对CPO指数保持强势",
        "回购方案获得董事会审议并披露明确价格、期限和资金安排"
      ],
      "invalidation": [
        "H股明显跌破暗盘低点并带动A股放量走弱",
        "A/H价差快速收敛主要通过A股下跌完成，且回购方案迟迟未落地"
      ],
      "urls": [
        "https://www.reuters.com/world/asia-pacific/zhongji-innolight-prices-hong-kong-listing-below-maximum-limit-raising-681-2026-07-27/",
        "https://wap.eastmoney.com/a/202607293825316172.html"
      ]
    },
    {
      "event": "三星创纪录利润确认存储景气，但兆易异常波动公告与涨价斜率放缓要求重新区分基本面和估值",
      "industry": "semi",
      "industry_name": "存储芯片",
      "direction": "mixed",
      "strength": 5,
      "horizon": "1-4w",
      "priced_in": "medium",
      "reason": "三星电子二季度经营利润同比大增19倍并创纪录，AI服务器需求继续支撑DRAM和NAND；TrendForce预计三季度传统DRAM合约价上涨13%-18%、NAND上涨10%-15%，方向仍向上但较二季度约60%的涨幅明显降速。兆易创新7月27日至29日累计价格偏离超过20%，公司公告称经营正常、无应披露未披露重大事项；7月29日股价仍下跌6.81%，说明长鑫上市后的资金与估值重构尚未结束。",
      "assets": [
        "603986",
        "001309",
        "600667"
      ],
      "validation": [
        "兆易创新、德明利相对存储指数止跌，三星和SK海力士的基本面利好获得日韩股价确认",
        "后续合约价与企业级SSD订单继续上修，太极实业获得扩产或封测订单验证"
      ],
      "invalidation": [
        "存储价格涨幅继续快速下修，消费电子客户因成本压力削减采购",
        "兆易创新继续弱于存储板块并出现新的公司级风险公告"
      ],
      "urls": [
        "https://www.reuters.com/world/asia-pacific/samsung-q2-profit-jumps-19-fold-ai-chip-demand-offsets-mobile-loss-2026-07-30/",
        "https://www.chnfund.com/article/ac955c4b-f8b8-e0e5-3a3a-3a22bff45859",
        "https://m.cls.cn/detail/2440172"
      ]
    }
  ]
};
