// 由 ChatGPT 网页版生成；新闻抓取工作流不会覆盖本文件。
window.AI_SIGNALS = {
  "generated_at": "2026-07-28 09:03",
  "source_generated_at": "2026-07-28 08:57",
  "generated_by": "ChatGPT Web",
  "status": "ready",
  "overseas_markets": [
    {
      "market": "美股",
      "flag": "🇺🇸",
      "session": "7月27日收盘",
      "updated_at": "2026-07-28 09:03 CST",
      "status": "negative",
      "status_label": "指数分化、芯片显著走弱",
      "move": "标普500 +0.02%｜道指 +0.51%｜纳指 -0.18%｜费城半导体 -2.20%；英伟达跌近5%",
      "driver": "长鑫科技首日暴涨强化全球存储竞争重估，叠加AI资本开支回报担忧，存储与芯片股集中下跌；油价大跌支撑大盘，但未能阻止半导体走弱。",
      "a_share_links": [
        "存储芯片",
        "CPO",
        "PCB",
        "半导体设备"
      ],
      "validation": "A股开盘后观察兆易创新、德明利是否继续弱于半导体指数，以及中际旭创、东山精密能否与存储链分化。",
      "sources": [
        "https://www.reuters.com/business/wall-st-futures-rise-us-iran-pause-hostilities-2026-07-27/",
        "https://apnews.com/article/stock-market-oil-iran-dow-nvidia-2026",
        "https://www.reuters.com/world/asia-pacific/china-memory-chipmaker-cxmt-set-shanghai-debut-after-asias-biggest-ipo-2026-07-26/"
      ]
    },
    {
      "market": "日股",
      "flag": "🇯🇵",
      "session": "7月28日早盘",
      "updated_at": "2026-07-28 09:48 JST",
      "status": "negative",
      "status_label": "低开后加速下跌",
      "move": "开盘64,539.92，前收64,931.19，跳空 -0.60%；09:48报62,253.24（-4.12%）",
      "driver": "隔夜美国半导体和AI权重下跌向亚洲传导，Advantest等芯片权重领跌；日经开盘价由日经官方与WSJ交叉核验一致。",
      "a_share_links": [
        "半导体设备",
        "存储芯片",
        "被动元件",
        "电子材料"
      ],
      "validation": "午前观察日经能否收复开盘价，以及Advantest、东京电子、铠侠是否止跌；A股重点比较太极实业、风华高科与各自行业指数。",
      "sources": [
        "https://indexes.nikkei.co.jp/en/nkave/index/profile",
        "https://www.wsj.com/market-data/quotes/index/JP/NIK/historical-prices",
        "https://www.jpx.co.jp/english/markets/indices/realvalues/01.html"
      ]
    },
    {
      "market": "韩股",
      "flag": "🇰🇷",
      "session": "7月28日早盘",
      "updated_at": "2026-07-28 09:39 KST",
      "status": "negative",
      "status_label": "大幅低开并继续下探",
      "move": "开盘6,400.27，前收6,755.75，跳空 -5.26%；09:39报6,273.84（-7.13%）",
      "driver": "隔夜英伟达、美光、SK海力士ADR等芯片股下跌，全球存储竞争和高估值风险重新定价；KOSPI开盘价、前收及早盘跌幅由WSJ与Investing.com交叉核验。",
      "a_share_links": [
        "存储芯片",
        "HBM",
        "封测",
        "AI服务器"
      ],
      "validation": "观察三星电子、SK海力士能否率先止跌，KOSPI能否收复开盘价；A股关注兆易创新、德明利、太极实业的相对强弱。",
      "sources": [
        "https://data.krx.co.kr/",
        "https://www.wsj.com/market-data/quotes/index/KR/SEU/historical-prices",
        "https://www.investing.com/indices/kospi"
      ]
    }
  ],
  "signals": [
    {
      "event": "长鑫科技首日暴涨466%，兆易创新跌停，国产存储进入资金与估值替代重定价",
      "industry": "semi",
      "industry_name": "半导体",
      "direction": "negative",
      "strength": 5,
      "horizon": "1-5d",
      "priced_in": "medium",
      "reason": "长鑫科技首日收于49元，较8.66元发行价上涨约466%，估值约3.3万亿元；同期兆易创新一度跌停。长鑫流通比例仅约6.73%，小流通盘放大首日价格弹性，并吸走存储链活跃资金。兆易创新持有长鑫约1.8%，但相关投资采用权益工具公允价值计量，估值变化不等同于主营利润同步兑现。隔夜全球存储股随后普跌，说明长鑫高估值已从A股内部比价扩展为全球竞争重估。",
      "assets": [
        "603986",
        "001309",
        "600667"
      ],
      "validation": [
        "长鑫次日成交与价格趋于稳定，兆易创新不再显著弱于存储指数",
        "德明利、太极实业获得扩产或产业订单逻辑承接，而非仅跟随资金炒作"
      ],
      "invalidation": [
        "长鑫继续大幅上涨并持续抽离存储链资金，兆易创新、德明利同步弱于行业",
        "后续披露显示长鑫扩产节奏或供应链外溢低于预期"
      ],
      "urls": [
        "https://www.reuters.com/world/asia-pacific/china-memory-chipmaker-cxmt-set-shanghai-debut-after-asias-biggest-ipo-2026-07-26/",
        "https://www.stcn.com/article/detail/4042794.html",
        "https://www.21jingji.com/article/20260527/herald/c30081bdae990276d65b84dd27feb6bd.html"
      ]
    },
    {
      "event": "全球芯片抛售扩散至日股和韩股，昨日韩国HBM合作利好被价格反转",
      "industry": "semi",
      "industry_name": "半导体",
      "direction": "negative",
      "strength": 5,
      "horizon": "intraday",
      "priced_in": "low",
      "reason": "隔夜费城半导体指数跌2.2%、英伟达跌近5%，存储相关公司跌幅更大。今早日经低开0.60%后跌约4.12%，KOSPI低开5.26%后跌约7.13%。这使昨天的韩国AI/HBM合作从产业利好转为价格未承接，并对A股存储、封测、CPO、PCB和被动元件形成明显负面外围映射；A股尚未开盘，实际传导待验证。",
      "assets": [
        "603986",
        "001309",
        "600667",
        "300308",
        "002384",
        "000636"
      ],
      "validation": [
        "三星电子、SK海力士及日股芯片权重止跌，日韩指数收复开盘价",
        "A股半导体、CPO、PCB出现独立承接，跟踪标的相对行业指数不再恶化"
      ],
      "invalidation": [
        "日韩芯片权重继续放量下跌，A股科技开盘同步出现普遍性抛售",
        "海外云厂商财报进一步下修AI资本开支或服务器需求预期"
      ],
      "urls": [
        "https://www.reuters.com/business/wall-st-futures-rise-us-iran-pause-hostilities-2026-07-27/",
        "https://indexes.nikkei.co.jp/en/nkave/index/profile",
        "https://www.wsj.com/market-data/quotes/index/KR/SEU/historical-prices"
      ]
    },
    {
      "event": "油价延续大跌、黄金回升，但FOMC加息风险令跨资产方向继续分化",
      "industry": "macro",
      "industry_name": "宏观 / 商品",
      "direction": "mixed",
      "strength": 4,
      "horizon": "1-5d",
      "priced_in": "medium",
      "reason": "布伦特原油周一下跌约8.7%，今早继续运行在88美元下方，供应冲击与通胀压力较上周明显缓和；黄金重新站上4100美元附近。与此同时，市场对本周美联储维持利率与加息25个基点仍存在分歧，利率结果将决定黄金和高估值科技的后续方向。国投白银LOF 7月27日收盘1.876元、实时估值约1.631元，估算溢价仍约15.02%，本体上涨不能消除场内价差风险。",
      "assets": [
        "300308",
        "002384"
      ],
      "validation": [
        "布伦特维持在90美元下方、美债收益率不再上冲，成长估值压力缓和",
        "国投白银LOF开盘后场内价格、当日估值与实际溢价同步回落"
      ],
      "invalidation": [
        "中东局势重新升级并推动油价快速反弹",
        "美联储加息或释放超预期鹰派路径，美元与实际利率重新上行"
      ],
      "urls": [
        "https://www.reuters.com/business/wall-st-futures-rise-us-iran-pause-hostilities-2026-07-27/",
        "https://www.haoetf.com/lof/161226",
        "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
      ]
    }
  ]
};
