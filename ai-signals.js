// 由 ChatGPT 网页版生成；新闻抓取工作流不会覆盖本文件。
window.AI_SIGNALS = {
  "generated_at": "2026-07-23 09:30",
  "source_generated_at": "2026-07-22 14:42",
  "generated_by": "ChatGPT Web",
  "status": "ready",
  "overseas_markets": [
    {
      "market": "美股",
      "flag": "🇺🇸",
      "session": "7月22日隔夜收盘",
      "updated_at": "2026-07-23 09:15",
      "status": "mixed",
      "status_label": "结构分化",
      "move": "标普 -0.14%｜纳指 -0.57%｜费城半导体 +0.4%",
      "driver": "服务器硬件受订单与业绩预期推动明显走强，但科技指数整体偏弱，AI需求验证与成长估值压力并存。",
      "a_share_links": [
        "CPO",
        "PCB",
        "AI服务器"
      ],
      "validation": "观察中际旭创、东山精密能否相对创业板与行业指数转强。",
      "sources": [
        "https://www.reuters.com/legal/transactional/wall-st-futures-edge-lower-caution-builds-ahead-big-tech-earnings-2026-07-22/"
      ]
    },
    {
      "market": "日股",
      "flag": "🇯🇵",
      "session": "7月23日开盘后",
      "updated_at": "2026-07-23 10:26 JST",
      "status": "positive",
      "status_label": "半导体领涨",
      "move": "日经开盘 66,421.01（较前收 +0.46%）｜10:26 报 66,759.89（+0.97%）",
      "driver": "日经官方开盘价与 WSJ 报价一致；AI资本开支预期带动芯片股，早盘 Renesas 约 +2.5%、Lasertec 约 +6.5%。",
      "a_share_links": [
        "半导体设备",
        "测试设备",
        "存储芯片",
        "被动元件"
      ],
      "validation": "观察东京电子、爱德万测试和铠侠能否维持强于日经，并映射A股设备、存储及风华高科的相对强弱。",
      "sources": [
        "https://indexes.nikkei.co.jp/en/nkave/index/profile",
        "https://www.wsj.com/market-data/quotes/index/JP/NIK/historical-prices",
        "https://www.jpx.co.jp/english/markets/indices/realvalues/01.html"
      ]
    },
    {
      "market": "韩股",
      "flag": "🇰🇷",
      "session": "7月23日开盘后",
      "updated_at": "2026-07-23 09:40 KST",
      "status": "positive",
      "status_label": "存储领涨",
      "move": "KOSPI 开盘 6,963.35（较前收 +2.44%）｜09:40 报 7,012.84（+3.16%）",
      "driver": "WSJ 与 Investing.com 对开盘价、前收和日内低点一致；Alphabet上调AI资本开支预期后，三星电子、SK海力士带动存储与HBM风险偏好修复。",
      "a_share_links": [
        "存储芯片",
        "HBM",
        "封测",
        "AI服务器"
      ],
      "validation": "重点比较三星电子、SK海力士相对KOSPI的强度，并观察兆易创新、德明利是否出现同步承接；韩国市场近期杠杆ETF监管会放大波动。",
      "sources": [
        "https://data.krx.co.kr/",
        "https://www.wsj.com/market-data/quotes/index/KR/SEU/historical-prices",
        "https://www.investing.com/indices/kospi"
      ]
    }
  ],
  "signals": [
    {
      "event": "A股科技修复未能延续，存储、CPO与半导体重新分化",
      "industry": "tech",
      "industry_name": "科技硬件",
      "direction": "negative",
      "strength": 4,
      "horizon": "1-5d",
      "priced_in": "unknown",
      "reason": "7月22日创业板与科创方向明显回落，存储芯片、PCB和光模块承压且高成交集中在科技龙头，说明前一日流动性修复尚未形成稳定趋势；今日开盘反馈待验证。",
      "assets": [
        "603986",
        "001309",
        "300308",
        "002384",
        "600667",
        "000636"
      ],
      "validation": [
        "开盘后多数标的继续弱于各自行业指数且高成交未形成承接",
        "存储、CPO、PCB与被动元件板块同步走弱"
      ],
      "invalidation": [
        "科技板块放量修复且核心标的收复7月22日主要跌幅",
        "行业内部出现明确业绩驱动的独立走强"
      ],
      "urls": [
        "https://finance.jrj.com.cn/2026/07/22152857873241.shtml",
        "https://www.mrjjxw.com/articles/2026-07-22/4495107.html"
      ]
    },
    {
      "event": "德明利再度跌停，存储景气与个股盈利持续性出现背离",
      "industry": "semi",
      "industry_name": "半导体",
      "direction": "negative",
      "strength": 5,
      "horizon": "1-5d",
      "priced_in": "unknown",
      "reason": "存储行业仍有价格与需求支撑，但德明利7月22日再度跌停，市场继续重估二季度利润持续性、估值和筹码结构，并对兆易创新等高弹性存储标的形成情绪映射；今日是否止跌待验证。",
      "assets": [
        "001309",
        "603986"
      ],
      "validation": [
        "德明利开盘后仍弱于存储板块且放量下行",
        "兆易创新同步弱于半导体指数，显示负面情绪扩散"
      ],
      "invalidation": [
        "德明利放量止跌并形成存储板块联动修复",
        "公司披露订单、毛利率或盈利持续性强于市场预期的新增证据"
      ],
      "urls": [
        "https://finance.jrj.com.cn/2026/07/22200557877032.shtml",
        "https://www.nbd.com.cn/articles/2026-07-21/4490883.html"
      ]
    },
    {
      "event": "美股服务器硬件大涨，但半导体指数仅小幅上行",
      "industry": "ai",
      "industry_name": "AI / 大模型",
      "direction": "mixed",
      "strength": 3,
      "horizon": "1-5d",
      "priced_in": "unknown",
      "reason": "Super Micro与Dell受订单和业绩预期推动显著上涨，验证AI服务器需求韧性；但纳指下跌、费城半导体指数仅涨0.4%，海外映射由全面修复转为个股分化，对A股CPO与PCB的传导需开盘确认。",
      "assets": [
        "300308",
        "002384"
      ],
      "validation": [
        "中际旭创、东山精密相对创业板和通信设备指数转强",
        "CPO与AI服务器链出现放量扩散而非单一个股脉冲"
      ],
      "invalidation": [
        "A股AI硬件高开低走并继续弱于大盘",
        "海外服务器硬件涨幅快速回吐或云厂商资本开支预期下修"
      ],
      "urls": [
        "https://www.reuters.com/legal/transactional/wall-st-futures-edge-lower-caution-builds-ahead-big-tech-earnings-2026-07-22/",
        "https://apnews.com/article/207dfa55d180fcc565420454178168c5"
      ]
    },
    {
      "event": "东山精密确认海外仓光模块被盗，需求景气与运营风险并存",
      "industry": "tech",
      "industry_name": "科技硬件",
      "direction": "mixed",
      "strength": 3,
      "horizon": "1-4w",
      "priced_in": "unknown",
      "reason": "公司证券部确认被盗事件属实，但称网传金额按销售价计算、利润影响不大且未达披露标准；同时公司交流称北美算力需求高度景气。事件增加库存、保险与交付核验需求，但现有信息不支持把网传巨额损失当作事实。",
      "assets": [
        "002384"
      ],
      "validation": [
        "公司后续公告或沟通确认损失、保险覆盖及交付影响",
        "东山精密相对PCB和CPO板块的开盘承接情况"
      ],
      "invalidation": [
        "公司确认损失已充分保险覆盖且不存在交付延迟",
        "后续经营数据继续验证光模块订单与利润兑现"
      ],
      "urls": [
        "https://www.nbd.com.cn/articles/2026-07-22/4498346.html",
        "https://finance.cnr.cn/gundong/20260722/t20260722_527723140.shtml"
      ]
    }
  ]
};
