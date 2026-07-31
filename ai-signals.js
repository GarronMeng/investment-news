// 由 ChatGPT 网页版生成；新闻抓取工作流不会覆盖本文件。
window.AI_SIGNALS = {
  "generated_at": "2026-07-31 09:10",
  "source_generated_at": "2026-07-30 17:45",
  "generated_by": "ChatGPT Web",
  "status": "ready",
  "overseas_markets": [
    {
      "market": "美股",
      "flag": "🇺🇸",
      "session": "7月30日收盘",
      "updated_at": "2026-07-31 09:10 CST",
      "status": "positive",
      "status_label": "微软带动AI与芯片强劲反弹",
      "move": "标普500 +1.66%｜道指 +1.19%｜纳指 +2.78%｜费城半导体 +8.2%",
      "driver": "微软上涨15.5%，强劲Azure增长与更克制的资本开支缓解了AI投资回报担忧；美光、闪迪和AMD同步大涨。盘后Amazon因AWS增长37%并上调AI基础设施投入而上涨约9%，Apple则因后续指引偏弱而下跌，科技内部仍有分化。",
      "a_share_links": [
        "CPO",
        "PCB",
        "存储芯片",
        "消费电子"
      ],
      "validation": "A股开盘后观察中际旭创、东山精密能否结束补跌并同步海外AI硬件反弹；同时观察兆易创新、德明利能否延续昨日存储修复。",
      "sources": [
        "https://www.reuters.com/business/us-stock-futures-steady-microsoft-offsets-fed-concerns-2026-07-30/",
        "https://apnews.com/article/b4ce02b4666a35b8975823c5c22072ee",
        "https://www.theguardian.com/technology/2026/jul/30/apple-amazon-second-quarter-revenues"
      ]
    },
    {
      "market": "日股",
      "flag": "🇯🇵",
      "session": "7月31日早盘",
      "updated_at": "2026-07-31 09:31 JST",
      "status": "positive",
      "status_label": "AI与半导体权重急升",
      "move": "开盘61,957.10，前收61,867.43，跳空 +0.14%；09:31报65,095.09（+5.22%）",
      "driver": "日经小幅高开后快速拉升，微软与美股芯片反弹带动软银、东京电子和Advantest等AI硬件权重。日经官方与WSJ对交易日期、开盘和前收一致；WSJ在09:16报63,981.14（+3.42%），因观测时刻不同分别保留。",
      "a_share_links": [
        "半导体设备",
        "存储芯片",
        "被动元件",
        "AI服务器"
      ],
      "validation": "观察日经午前能否守住开盘后的主要涨幅，以及东京电子、Advantest和铠侠是否同步维持强势；A股关注太极实业、风华高科及存储链承接。",
      "sources": [
        "https://indexes.nikkei.co.jp/en/nkave/index/profile",
        "https://www.wsj.com/market-data/quotes/index/JP/NIK/historical-prices",
        "https://www.jpx.co.jp/english/markets/indices/realvalues/01.html"
      ]
    },
    {
      "market": "韩股",
      "flag": "🇰🇷",
      "session": "7月31日早盘",
      "updated_at": "2026-07-31 09:39 KST",
      "status": "positive",
      "status_label": "芯片权重推动暴力修复",
      "move": "开盘5,681.77，前收5,593.56，跳空 +1.58%；09:39报6,413.63（+14.66%）",
      "driver": "三星电子与SK海力士大幅反弹，微软财报、美股芯片上涨及两家公司创纪录利润共同驱动KOSPI修复。WSJ与AP方向一致，但当前涨幅属于此前连续暴跌后的高波动反弹，不能直接视为趋势反转。",
      "a_share_links": [
        "存储芯片",
        "HBM",
        "封测",
        "AI服务器"
      ],
      "validation": "观察KOSPI是否触发或接近波动管理措施后仍能守住开盘价，三星电子与SK海力士是否保持成交承接；A股关注兆易创新、德明利、太极实业是否同步。",
      "sources": [
        "https://data.krx.co.kr/",
        "https://www.wsj.com/market-data/quotes/index/KR/SEU/historical-prices",
        "https://apnews.com/article/e31b3a442bcb957a53f1823ef21e73e8"
      ]
    }
  ],
  "signals": [
    {
      "event": "Amazon上调AI资本开支至2200亿美元，AWS加速增长进一步验证云端基础设施需求",
      "industry": "ai",
      "industry_name": "AI基础设施",
      "direction": "positive",
      "strength": 5,
      "horizon": "1-4w",
      "priced_in": "low",
      "reason": "Amazon二季度AWS收入同比增长37%至422亿美元，为18个季度以来最快增速；公司将2026年资本开支计划由2000亿美元提高至2200亿美元，并称AI算力到2028年仍存在强劲需求和容量约束。叠加微软Azure增长43%，云厂商需求端从单纯投入承诺转向收入兑现，对高速光模块、服务器PCB和数据中心网络需求形成更直接验证。",
      "assets": [
        "300308",
        "002384"
      ],
      "validation": [
        "中际旭创、东山精密相对CPO和PCB指数止跌转强，海外财报利好不再伴随A股冲高回落",
        "后续云厂商继续确认1.6T光模块、交换机和AI服务器采购节奏"
      ],
      "invalidation": [
        "Amazon盘后涨幅明显回吐，市场重新聚焦负自由现金流和债务融资压力",
        "云厂商虽上调资本开支，但供应链公司下修订单、价格或交付预期"
      ],
      "urls": [
        "https://apnews.com/article/b4ce02b4666a35b8975823c5c22072ee",
        "https://www.ft.com/content/fddc42a9-4c57-4689-abde-75bbe79622e9",
        "https://www.reuters.com/business/us-stock-futures-steady-microsoft-offsets-fed-concerns-2026-07-30/"
      ]
    },
    {
      "event": "海外芯片暴力反弹，但A股昨日仍呈现存储修复与CPO、PCB继续补跌的结构分化",
      "industry": "tech",
      "industry_name": "AI硬件 / 半导体",
      "direction": "mixed",
      "strength": 5,
      "horizon": "intraday",
      "priced_in": "medium",
      "reason": "隔夜费城半导体指数上涨8.2%，今早日经和KOSPI在芯片权重带动下急升；但7月30日A股中际旭创成交超过597亿元并继续大幅波动，东山精密再次跌停，而存储链午后率先回流，德明利涨停、兆易创新收涨1.94%。这说明海外风险偏好已明显修复，但A股资金仍在高位CPO、PCB与较早调整的存储之间重新配置，今日价格联动才是反转是否成立的关键。",
      "assets": [
        "603986",
        "001309",
        "300308",
        "002384",
        "600667"
      ],
      "validation": [
        "中际旭创、东山精密不再出现放量补跌，且能与日韩AI硬件同步修复",
        "兆易创新、德明利守住昨日反弹成果，太极实业获得存储和封测链扩散"
      ],
      "invalidation": [
        "海外指数高开大幅回落，A股CPO与PCB继续出现批量跌停或天量下跌",
        "存储链昨日反弹一日游，兆易创新和德明利重新跌破前一日低点"
      ],
      "urls": [
        "https://www.reuters.com/business/us-stock-futures-steady-microsoft-offsets-fed-concerns-2026-07-30/",
        "https://www.cls.cn/detail/2440883",
        "https://apnews.com/article/e31b3a442bcb957a53f1823ef21e73e8"
      ]
    },
    {
      "event": "Apple当季iPhone需求强劲但后续指引低于预期，消费电子映射由需求确认转为持续性验证",
      "industry": "consumer",
      "industry_name": "消费电子 / 被动元件",
      "direction": "mixed",
      "strength": 4,
      "horizon": "1-4w",
      "priced_in": "low",
      "reason": "Apple季度收入同比增长16.4%至1094亿美元，iPhone收入增长21.7%至543亿美元，验证高端终端需求；但下一季度收入增长指引为9%-11%，低于市场约12.1%的预期，且公司提示零部件短缺和汇率压力，盘后股价下跌。对东山精密、风华高科而言，当前订单需求偏正面，但持续性、供应约束和成本传导仍需确认。",
      "assets": [
        "002384",
        "000636"
      ],
      "validation": [
        "消费电子、FPC和被动元件板块形成同步承接，东山精密与风华高科相对行业指数改善",
        "后续供应链订单、备货和MLCC渠道数据确认需求没有因成本上涨而下修"
      ],
      "invalidation": [
        "Apple供应链继续下修后续季度订单，零部件短缺明显限制出货",
        "强劲当季收入未能阻止相关供应链股票继续放量下跌"
      ],
      "urls": [
        "https://www.theguardian.com/technology/2026/jul/30/apple-amazon-second-quarter-revenues",
        "https://www.thetimes.com/business/companies-markets/article/apple-earnings-iphone-sales-tim-cook-rdbjzjxjz"
      ]
    }
  ]
};
