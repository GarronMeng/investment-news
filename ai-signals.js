// 由 ChatGPT 网页版生成；新闻抓取工作流不会覆盖本文件。
window.AI_SIGNALS = {
  "generated_at": "2026-07-26 09:09",
  "source_generated_at": "2026-07-25 17:14",
  "generated_by": "ChatGPT Web",
  "status": "ready",
  "overseas_markets": [
    {
      "market": "美股",
      "flag": "🇺🇸",
      "session": "7月24日收盘；周末休市",
      "updated_at": "2026-07-26 09:09 CST",
      "status": "mixed",
      "status_label": "指数企稳、科技仍弱",
      "move": "标普 +0.05%｜道指 +0.46%｜纳指 -0.64%；本周标普 -0.6%、道指 -0.4%、纳指 -2.1%",
      "driver": "油价从100美元上方回落使大盘企稳，但芯片与AI资本开支回报担忧继续压制纳指；下周FOMC和微软、Meta、Amazon、Apple财报将重新定价AI需求与利率。",
      "a_share_links": [
        "CPO",
        "PCB",
        "AI服务器",
        "成长估值"
      ],
      "validation": "周一先看美股股指期货、油价和美债收益率；随后关注云厂商资本开支、数据中心部署与AI收入指引。",
      "sources": [
        "https://www.reuters.com/world/china/global-markets-global-markets-2026-07-24/",
        "https://apnews.com/article/02d01b8f38ccd51f605c4414cdd4fa9b",
        "https://www.reuters.com/business/wall-st-week-ahead-us-stocks-face-tests-fed-decision-tech-led-earnings-deluge-2026-07-24/"
      ]
    },
    {
      "market": "日股",
      "flag": "🇯🇵",
      "session": "7月24日收盘；周末休市",
      "updated_at": "2026-07-24 15:00 JST",
      "status": "negative",
      "status_label": "半导体拖累",
      "move": "开盘65,584.25，前收66,422.60，跳空-1.26%；收报64,611.15（-2.73%）",
      "driver": "AI资本开支回报担忧打击半导体权重，Advantest、东京电子、软银和铠侠显著下跌；日经7月累计回撤接近8%，进入技术性调整区间。",
      "a_share_links": [
        "半导体设备",
        "存储芯片",
        "被动元件",
        "电子材料"
      ],
      "validation": "周一观察铠侠、东京电子与Advantest能否相对日经止跌，并比较A股存储、太极实业和风华高科的开盘反馈。",
      "sources": [
        "https://www.reuters.com/world/asia-pacific/japans-nikkei-falls-more-than-2-ai-spending-worries-2026-07-24/",
        "https://indexes.nikkei.co.jp/en/nkave/index/profile",
        "https://www.wsj.com/market-data/quotes/index/JP/NIK/historical-prices"
      ]
    },
    {
      "market": "韩股",
      "flag": "🇰🇷",
      "session": "7月24日收盘；周末休市",
      "updated_at": "2026-07-26 09:09 CST",
      "status": "mixed",
      "status_label": "暴跌后迎来HBM催化",
      "move": "开盘7,000.78，前收7,096.89，跳空-1.35%；收报6,690.62（-5.72%）",
      "driver": "周五芯片权重推动KOSPI大跌；周末韩国宣布SK海力士与英伟达、三星与博通的AI/HBM、存储、先进封装及数据中心合作，形成周一正面基本面催化但高波动风险仍在。",
      "a_share_links": [
        "存储芯片",
        "HBM",
        "封测",
        "AI服务器"
      ],
      "validation": "周一核验三星电子、SK海力士能否放量修复，以及兆易创新、德明利、太极实业和AI硬件链是否出现同步承接。",
      "sources": [
        "https://data.krx.co.kr/",
        "https://en.sedaily.com/finance/2026/07/24/kospi-closes-down-40627-points-at-669062",
        "https://www.reuters.com/business/media-telecom/south-korea-president-lee-looking-open-new-era-ai-with-global-tech-companies-2026-07-25/"
      ]
    }
  ],
  "signals": [
    {
      "event": "韩国公布三星、SK与美国科技公司的AI、HBM和数据中心合作",
      "industry": "semi",
      "industry_name": "半导体",
      "direction": "positive",
      "strength": 5,
      "horizon": "1-3m",
      "priced_in": "unknown",
      "reason": "韩国方面宣布SK集团约7500亿美元合作，其中SK海力士与英伟达涉及约5000亿美元HBM和数据中心项目；三星与博通签署约2000亿美元AI加速器、存储、晶圆代工和先进封装合作，并规划2GW AI数据中心。该消息发生在KOSPI周五下跌5.72%之后，对存储、HBM、封测、高速互联和PCB形成新增需求证据，周一价格反馈待验证。",
      "assets": [
        "603986",
        "001309",
        "600667",
        "300308",
        "002384"
      ],
      "validation": [
        "三星电子、SK海力士周一放量修复，A股存储、封测、CPO和PCB同步转强",
        "后续披露可执行订单、建设周期、资本开支和供货份额"
      ],
      "invalidation": [
        "合作仅停留在框架或备忘录层面，金额与执行节奏明显下修",
        "韩股芯片权重继续下跌且A股相关链条对消息无承接"
      ],
      "urls": [
        "https://www.reuters.com/business/media-telecom/south-korea-president-lee-looking-open-new-era-ai-with-global-tech-companies-2026-07-25/",
        "https://www.reuters.com/world/asia-pacific/samsung-sk-hynix-announce-major-chip-deals-with-us-tech-companies-seoul-says-2026-07-24/",
        "https://www.reuters.com/business/energy/power-water-needs-test-south-koreas-push-build-ai-chip-hub-beyond-seoul-2026-07-21/"
      ]
    },
    {
      "event": "Apple与Micron围绕中国存储供应商展开政策博弈",
      "industry": "semi",
      "industry_name": "半导体",
      "direction": "mixed",
      "strength": 4,
      "horizon": "1-4w",
      "priced_in": "unknown",
      "reason": "Apple希望获准在非美国市场使用长鑫存储和长江存储产品，以缓解存储短缺与成本上涨；Micron则从产业安全和美国本土制造角度反对。事件同时强化中国存储产品的成本竞争力与全球客户需求，也带来美国审批、制裁和供应链准入不确定性。",
      "assets": [
        "603986",
        "001309",
        "600667"
      ],
      "validation": [
        "美国政府明确审批范围，或Apple、供应商披露实际采购与认证进展",
        "存储价格、国产存储板块及兆易创新、德明利相对半导体指数转强"
      ],
      "invalidation": [
        "审批被明确否决或限制扩大至更多中国存储产品",
        "全球存储供需转松、价格回落削弱成本驱动"
      ],
      "urls": [
        "https://www.wsj.com/tech/trump-apple-micron-china-chips-784bbd3d",
        "https://www.reuters.com/commentary/breakingviews/apples-china-plea-signals-low-tech-chip-upheaval-2026-07-15/",
        "https://www.reuters.com/world/asia-pacific/apple-seeks-approval-buy-chips-blacklisted-chinese-company-ft-reports-2026-06-27/"
      ]
    },
    {
      "event": "FOMC与大型科技公司财报构成下周AI资本开支集中验证窗口",
      "industry": "ai",
      "industry_name": "AI / 大模型",
      "direction": "mixed",
      "strength": 5,
      "horizon": "1-5d",
      "priced_in": "unknown",
      "reason": "美联储7月28至29日议息，市场主要预期维持利率但油价、关税和通胀令鹰派风险上升；微软和Meta于7月29日、Amazon与Apple于7月30日披露业绩。云资本开支、AI收入、数据中心建设及利率路径将共同影响CPO、PCB和高估值科技定价。",
      "assets": [
        "300308",
        "002384",
        "603986",
        "001309"
      ],
      "validation": [
        "微软、Meta、Amazon继续上调或维持AI资本开支，且给出数据中心、高速互联或服务器需求证据",
        "FOMC未释放超预期鹰派信号，美债收益率与美元未进一步上冲"
      ],
      "invalidation": [
        "云厂商下修资本开支或AI回报指引，硬件订单出现延迟",
        "美联储意外加息或明显强化近期加息预期"
      ],
      "urls": [
        "https://www.reuters.com/business/wall-st-week-ahead-us-stocks-face-tests-fed-decision-tech-led-earnings-deluge-2026-07-24/",
        "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        "https://news.microsoft.com/source/2026/07/08/microsoft-announces-quarterly-earnings-release-date-68/"
      ]
    }
  ]
};
