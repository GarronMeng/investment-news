// 由 ChatGPT 网页版生成；新闻抓取工作流不会覆盖本文件。
window.AI_SIGNALS = {
  "generated_at": "2026-07-27 09:16",
  "source_generated_at": "2026-07-27 09:09",
  "generated_by": "ChatGPT Web",
  "status": "ready",
  "overseas_markets": [
    {
      "market": "美股",
      "flag": "🇺🇸",
      "session": "7月24日收盘；7月27日亚洲时段期货",
      "updated_at": "2026-07-27 09:16 CST",
      "status": "mixed",
      "status_label": "现货科技偏弱、期货修复",
      "move": "周五标普 +0.05%｜道指 +0.46%｜纳指 -0.64%；今早标普500期货约 +0.8%、纳指期货约 +1.3%",
      "driver": "海湾局势暂缓令油价大跌、通胀担忧降温，美债收益率回落，股指期货修复；但周五美光、闪迪及多只AI硬件股明显下跌，本周FOMC和大型科技财报仍是关键验证。",
      "a_share_links": [
        "CPO",
        "PCB",
        "AI服务器",
        "成长估值"
      ],
      "validation": "A股开盘后观察中际旭创、东山精密能否同步股指期货修复；随后关注微软、Meta、Amazon、Apple资本开支和FOMC利率信号。",
      "sources": [
        "https://www.investing.com/news/stock-market-news/shares-bonds-bounce-as-oil-skid-offers-inflation-relief-4812933",
        "https://www.reuters.com/business/wall-st-week-ahead-us-stocks-face-tests-fed-decision-tech-led-earnings-deluge-2026-07-24/",
        "https://www.wsj.com/market-data/quotes/index/US/COMP"
      ]
    },
    {
      "market": "日股",
      "flag": "🇯🇵",
      "session": "7月27日早盘",
      "updated_at": "2026-07-27 10:14 JST",
      "status": "mixed",
      "status_label": "高开后转跌",
      "move": "开盘65,164.98，前收64,611.15，跳空 +0.86%；10:14报64,181.90（-0.66%）",
      "driver": "油价和收益率回落带来高开，但日经随后跌破前收，显示半导体与AI资本开支担忧尚未消退；早盘高低点波动超过1000点。",
      "a_share_links": [
        "半导体设备",
        "存储芯片",
        "被动元件",
        "电子材料"
      ],
      "validation": "午前观察铠侠、东京电子、Advantest能否止跌，并比较兆易创新、德明利、太极实业与风华高科的A股开盘反馈。",
      "sources": [
        "https://indexes.nikkei.co.jp/en/nkave/index/profile",
        "https://www.wsj.com/market-data/quotes/index/JP/NIK/historical-prices",
        "https://www.jpx.co.jp/english/markets/indices/realvalues/01.html"
      ]
    },
    {
      "market": "韩股",
      "flag": "🇰🇷",
      "session": "7月27日早盘",
      "updated_at": "2026-07-27 09:44 KST",
      "status": "positive",
      "status_label": "高开、涨幅收窄",
      "move": "开盘6,806.27，前收6,690.62，跳空 +1.73%；09:44报6,725.17（+0.52%）",
      "driver": "周末三星、SK海力士与美国科技公司的AI/HBM合作带来开盘修复，但指数较开盘明显回落，表明长期产业催化与短线筹码压力并存。",
      "a_share_links": [
        "存储芯片",
        "HBM",
        "封测",
        "AI服务器"
      ],
      "validation": "继续核验三星电子、SK海力士的成交和相对强度；A股开盘后观察兆易创新、德明利、太极实业及AI硬件链是否同步承接。",
      "sources": [
        "https://data.krx.co.kr/",
        "https://www.wsj.com/market-data/quotes/index/KR/SEU/historical-prices",
        "https://www.investing.com/indices/kospi"
      ]
    }
  ],
  "signals": [
    {
      "event": "长鑫科技今日登陆科创板，国产DRAM进入直接市场定价窗口",
      "industry": "semi",
      "industry_name": "半导体",
      "direction": "mixed",
      "strength": 5,
      "horizon": "intraday",
      "priced_in": "unknown",
      "reason": "长鑫科技7月27日以8.66元发行价上市，募资579.2亿元（超额配售全额行使前），是今年亚洲最大IPO。上市提高国产DRAM的资本市场可见度，并为产线、研发和供应链扩张提供资金；同时其首日估值、成交规模和资金分流会直接影响存储链比价。A股尚未开盘，价格反馈待验证。",
      "assets": [
        "603986",
        "001309",
        "600667"
      ],
      "validation": [
        "长鑫科技首日成交活跃且价格保持相对稳定，兆易创新、德明利、太极实业相对半导体指数获得承接",
        "后续募投项目形成明确设备、材料、封测或工程订单"
      ],
      "invalidation": [
        "上市首日高开后快速回落并拖累存储链风险偏好",
        "募投项目进度或行业价格周期明显低于预期"
      ],
      "urls": [
        "https://www.reuters.com/world/asia-pacific/chinese-chipmaker-cxmt-list-shanghai-july-27-after-asias-biggest-ipo-this-year-2026-07-23/",
        "https://www.stcn.com/article/detail/4038311.html",
        "https://www.thepaper.cn/newsDetail_forward_33645240"
      ]
    },
    {
      "event": "韩国AI/HBM合作获得开盘承接，但KOSPI涨幅快速收窄",
      "industry": "semi",
      "industry_name": "半导体",
      "direction": "mixed",
      "strength": 4,
      "horizon": "1-5d",
      "priced_in": "low",
      "reason": "KOSPI在周五大跌5.72%后，受三星、SK海力士AI/HBM合作催化高开1.73%，但09:44涨幅已收窄至0.52%。这验证了产业消息的正面方向，也显示高波动和筹码压力尚未解除；对A股存储、封测、CPO和PCB的映射需要开盘后确认。",
      "assets": [
        "603986",
        "001309",
        "600667",
        "300308",
        "002384"
      ],
      "validation": [
        "三星电子、SK海力士午前维持相对强势，KOSPI不再跌破前收",
        "A股存储、封测、CPO和PCB相对各自指数转强"
      ],
      "invalidation": [
        "KOSPI重新转跌且芯片权重继续领跌",
        "合作金额或执行节奏在正式文件中明显下修"
      ],
      "urls": [
        "https://www.reuters.com/business/media-telecom/south-korea-president-lee-looking-open-new-era-ai-with-global-tech-companies-2026-07-25/",
        "https://www.wsj.com/market-data/quotes/index/KR/SEU/historical-prices",
        "https://www.investing.com/indices/kospi"
      ]
    },
    {
      "event": "海湾局势暂缓推动油价大跌，黄金白银与科技估值同步重定价",
      "industry": "macro",
      "industry_name": "宏观 / 商品",
      "direction": "mixed",
      "strength": 4,
      "horizon": "1-5d",
      "priced_in": "medium",
      "reason": "今早布伦特和WTI一度下跌约5%，10年期美债收益率回落约4个基点至4.63%，美元走弱；黄金上涨约1.4%、白银期货上涨约2%。油价回落减轻通胀和加息压力，支持高估值科技修复并利于黄金，但国投白银LOF截至7月24日仍有约14.21%场内溢价，基金价格不能只按银价判断。",
      "assets": [
        "300308",
        "002384"
      ],
      "validation": [
        "布伦特维持在100美元下方、美债收益率不再上冲，A股成长风格获得承接",
        "国投白银LOF场内价格、净值和溢价在开盘后同步核验"
      ],
      "invalidation": [
        "中东冲突重新升级并推动油价快速反弹",
        "美联储释放超预期鹰派信号，美元与实际利率重新上行"
      ],
      "urls": [
        "https://www.investing.com/news/stock-market-news/shares-bonds-bounce-as-oil-skid-offers-inflation-relief-4812933",
        "https://www.haoetf.com/lof/161226",
        "https://www.reuters.com/world/asia-pacific/iran-war-spreads-red-sea-caspian-gulf-quiet-us-forgoes-strikes-2026-07-25/"
      ]
    }
  ]
};
