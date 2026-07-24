// 由 ChatGPT 网页版生成；新闻抓取工作流不会覆盖本文件。
window.AI_SIGNALS = {
  "generated_at": "2026-07-24 09:21",
  "source_generated_at": "2026-07-24 08:56",
  "generated_by": "ChatGPT Web",
  "status": "ready",
  "overseas_markets": [
    {
      "market": "美股",
      "flag": "🇺🇸",
      "session": "7月23日隔夜收盘",
      "updated_at": "2026-07-24 09:21 CST",
      "status": "negative",
      "status_label": "科技与利率双压",
      "move": "标普 -1.21%｜纳指 -2.15%｜道指 -0.97%｜布伦特原油升破100美元",
      "driver": "Alphabet与Tesla财报令市场重新评估AI资本开支回报；中东与贸易风险推升油价、通胀和利率预期，成长估值与科技风险偏好同步承压。",
      "a_share_links": [
        "CPO",
        "PCB",
        "AI服务器",
        "成长估值"
      ],
      "validation": "观察中际旭创、东山精密能否相对创业板与科技硬件指数抗跌，以及油价和美债收益率是否继续上行。",
      "sources": [
        "https://www.reuters.com/world/china/global-markets-wrapup-1-2026-07-23/",
        "https://www.reuters.com/business/autos-transportation/wall-st-futures-ease-big-tech-results-revive-ai-spending-worries-oil-jumps-2026-07-23/",
        "https://apnews.com/article/45b9165d6c518f5bea668b6ba7a89838"
      ]
    },
    {
      "market": "日股",
      "flag": "🇯🇵",
      "session": "7月24日开盘后",
      "updated_at": "2026-07-24 10:03 JST",
      "status": "negative",
      "status_label": "跳空下跌",
      "move": "开盘65,584.25，前收66,422.60，跳空-1.26%；09:47日经官方报64,901.82（-2.29%），10:03 WSJ报64,688.84（-2.61%）",
      "driver": "两个报价源对开盘价与前收一致；隔夜美股科技下跌、油价和收益率上行压制日本半导体与高估值出口链，日元弱势未能抵消风险偏好冲击。",
      "a_share_links": [
        "半导体设备",
        "存储芯片",
        "被动元件",
        "电子材料"
      ],
      "validation": "观察日本半导体设备、测试及材料股是否继续弱于日经，并比较A股太极实业、风华高科及存储链的相对表现。",
      "sources": [
        "https://indexes.nikkei.co.jp/en/nkave/index/profile",
        "https://www.wsj.com/market-data/quotes/index/JP/NIK/historical-prices",
        "https://www.jpx.co.jp/english/markets/indices/realvalues/01.html"
      ]
    },
    {
      "market": "韩股",
      "flag": "🇰🇷",
      "session": "7月24日开盘后",
      "updated_at": "2026-07-24 09:37 KST",
      "status": "negative",
      "status_label": "存储权重回撤",
      "move": "开盘7,000.78，前收7,096.89，跳空-1.35%；09:37 WSJ报6,834.42（-3.70%）；第二来源核对开盘价与前收一致",
      "driver": "隔夜美国科技股下挫及油价、收益率上行触发风险回撤；KOSPI在此前快速反弹后转弱，对三星电子、SK海力士及存储/HBM链的当日精确幅度仍需盘中继续核验。",
      "a_share_links": [
        "存储芯片",
        "HBM",
        "封测",
        "AI服务器"
      ],
      "validation": "继续核验三星电子、SK海力士相对KOSPI的表现，并观察兆易创新、德明利能否摆脱韩股存储权重下跌的情绪映射。",
      "sources": [
        "https://data.krx.co.kr/",
        "https://www.wsj.com/market-data/quotes/index/KR/SEU/historical-prices",
        "https://www.investing.com/indices/kospi"
      ]
    }
  ],
  "signals": [
    {
      "event": "隔夜美股科技下挫，今晨日经与KOSPI同步跳空走弱",
      "industry": "tech",
      "industry_name": "科技硬件",
      "direction": "negative",
      "strength": 5,
      "horizon": "1-5d",
      "priced_in": "unknown",
      "reason": "纳指7月23日收跌2.15%，布伦特原油升破100美元；7月24日日经开盘跳空-1.26%、KOSPI开盘跳空-1.35%，开盘后跌幅扩大。外围由前一日半导体与存储修复转为同步风险回撤，对A股科技链的开盘传导尚待验证。",
      "assets": [
        "603986",
        "001309",
        "300308",
        "002384",
        "600667",
        "000636"
      ],
      "validation": [
        "A股存储、CPO、PCB、半导体工程及被动元件同步弱于主要指数",
        "日经与KOSPI午前继续扩大跌幅且海外芯片权重未出现相对修复"
      ],
      "invalidation": [
        "A股核心科技标的放量抗跌并形成独立于日韩市场的修复",
        "油价与美债收益率明显回落，海外科技期货转稳"
      ],
      "urls": [
        "https://www.reuters.com/world/china/global-markets-wrapup-1-2026-07-23/",
        "https://indexes.nikkei.co.jp/en/nkave/index/profile",
        "https://www.wsj.com/market-data/quotes/index/KR/SEU/historical-prices"
      ]
    },
    {
      "event": "A股普遍反弹但存储与MCU逆势偏弱，CPO相对有承接",
      "industry": "semi",
      "industry_name": "半导体",
      "direction": "mixed",
      "strength": 4,
      "horizon": "1-5d",
      "priced_in": "unknown",
      "reason": "7月23日A股约4260只个股上涨、主要指数小幅收涨，但存储芯片与MCU仍偏弱；兆易创新收跌3.84%，中际旭创则上涨约1.1%。这表明科技内部由系统性波动转向存储盈利持续性与AI硬件需求的分层定价，今日开盘延续性待验证。",
      "assets": [
        "603986",
        "001309",
        "300308",
        "002384"
      ],
      "validation": [
        "兆易创新、德明利继续弱于半导体指数，而中际旭创、东山精密相对抗跌",
        "存储与MCU成交放大但未形成有效修复"
      ],
      "invalidation": [
        "存储链放量反弹并收复7月23日主要跌幅",
        "CPO与PCB同步转弱，科技内部相对分化消失"
      ],
      "urls": [
        "https://m.21jingji.com/article/20260723/herald/764bd53bf22e28569ee17731af0a5f26.html",
        "https://finance.jrj.com.cn/2026/07/23174157882698.shtml"
      ]
    },
    {
      "event": "AMD Helios与OpenAI 3.2GW项目新增需求证据，资本回报担忧同步升温",
      "industry": "ai",
      "industry_name": "AI / 大模型",
      "direction": "mixed",
      "strength": 4,
      "horizon": "1-3m",
      "priced_in": "unknown",
      "reason": "AMD披露微软Azure计划在2026年下半年部署Helios机架级AI系统，OpenAI公布佐治亚州Project Camellia分阶段建设3.2GW数据中心，继续验证高速互联、PCB与服务器硬件的中期需求；但Alphabet与Tesla引发的资本支出回报担忧正压制短期估值。",
      "assets": [
        "300308",
        "002384"
      ],
      "validation": [
        "云厂商继续确认AI基础设施资本开支及部署进度，中际旭创、东山精密订单或指引获得验证",
        "A股CPO、PCB相对海外科技指数保持强势"
      ],
      "invalidation": [
        "主要云厂商下修AI资本开支或项目延期",
        "高速互联与PCB需求未能转化为相关公司订单、收入或利润改善"
      ],
      "urls": [
        "https://www.amd.com/zh-tw/newsroom/press-releases/2026-7-20-microsoft-to-deploy-next-gen-amd-instinct-and-amd-.html",
        "https://openai.com/index/building-ai-infrastructure-with-the-effingham-county-community/",
        "https://www.reuters.com/business/autos-transportation/wall-st-futures-ease-big-tech-results-revive-ai-spending-worries-oil-jumps-2026-07-23/"
      ]
    }
  ]
};
