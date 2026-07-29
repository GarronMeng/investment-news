// 由 ChatGPT 网页版生成；新闻抓取工作流不会覆盖本文件。
window.AI_SIGNALS = {
  "generated_at": "2026-07-29 09:07",
  "source_generated_at": "2026-07-29 08:58",
  "generated_by": "ChatGPT Web",
  "status": "ready",
  "overseas_markets": [
    {
      "market": "美股",
      "flag": "🇺🇸",
      "session": "7月28日收盘",
      "updated_at": "2026-07-29 09:07 CST",
      "status": "mixed",
      "status_label": "大盘企稳、芯片继续下挫",
      "move": "标普500 +0.21%｜道指 +1.03%｜纳指 -0.22%｜费城半导体 -4.50%",
      "driver": "医疗、必需消费和材料板块支撑大盘，但市场继续担忧AI数据中心投入回报、债务融资与中国半导体竞争；布伦特原油跌4.8%至84.09美元，缓和部分通胀压力。",
      "a_share_links": [
        "CPO",
        "PCB",
        "存储芯片",
        "半导体设备"
      ],
      "validation": "A股开盘后观察中际旭创、东山精密、兆易创新和德明利能否相对各自行业指数止跌；今晚FOMC及微软、Meta财报将验证利率和AI资本开支路径。",
      "sources": [
        "https://www.reuters.com/business/nasdaq-futures-drop-ai-chip-worries-ahead-pivotal-earnings-2026-07-28/",
        "https://www.wsj.com/livecoverage/stock-market-today-dow-sp-500-nasdaq-07-28-2026",
        "https://www.reuters.com/business/bar-fed-rate-hike-this-week-remains-high-even-markets-see-chance-2026-07-28/"
      ]
    },
    {
      "market": "日股",
      "flag": "🇯🇵",
      "session": "7月29日早盘",
      "updated_at": "2026-07-29 10:02 JST",
      "status": "mixed",
      "status_label": "高开后涨幅几乎回吐",
      "move": "开盘62,734.68，前收62,364.92，跳空 +0.59%；10:02报62,430.56（+0.11%）",
      "driver": "日经在昨日大跌后出现超跌反弹，但盘中一度由高点63,138.04回落至62,343.75，说明芯片与AI硬件风险偏好尚未稳定；开盘和实时点位来自日经官方，WSJ用于复核前收与开盘。",
      "a_share_links": [
        "半导体设备",
        "存储芯片",
        "被动元件",
        "电子材料"
      ],
      "validation": "观察日经能否重新站稳开盘价，以及东京电子、Advantest、铠侠能否维持反弹；A股关注太极实业、风华高科相对行业指数的承接。",
      "sources": [
        "https://indexes.nikkei.co.jp/en/nkave/index/profile",
        "https://www.wsj.com/market-data/quotes/index/JP/NIK/historical-prices",
        "https://www.jpx.co.jp/english/markets/indices/realvalues/01.html"
      ]
    },
    {
      "market": "韩股",
      "flag": "🇰🇷",
      "session": "7月29日早盘",
      "updated_at": "2026-07-29 09:17 KST",
      "status": "mixed",
      "status_label": "暴跌后反弹、尚未扭转弱势",
      "move": "开盘6,089.11，前收6,023.66，跳空 +1.09%；09:17报6,155.57（+2.19%）",
      "driver": "KOSPI在昨日下跌10.84%、三星电子和SK海力士大跌后出现技术性修复，但当前涨幅只收复前一日跌幅的一小部分；WSJ与Investing.com对开盘和前收一致，当前报价因观测时刻不同分别保留。",
      "a_share_links": [
        "存储芯片",
        "HBM",
        "封测",
        "AI服务器"
      ],
      "validation": "观察三星电子、SK海力士和KOSPI能否守住开盘价并扩大反弹；A股关注兆易创新、德明利、太极实业是否出现独立止跌。",
      "sources": [
        "https://data.krx.co.kr/",
        "https://www.wsj.com/market-data/quotes/index/KR/SEU/historical-prices",
        "https://www.investing.com/indices/kospi"
      ]
    }
  ],
  "signals": [
    {
      "event": "A股AI硬件与存储出现集中去杠杆，今早日韩仅呈现部分超跌修复",
      "industry": "tech",
      "industry_name": "AI硬件 / 半导体",
      "direction": "mixed",
      "strength": 5,
      "horizon": "intraday",
      "priced_in": "medium",
      "reason": "7月28日创业板指下跌7.35%，中际旭创跌逾15%、东山精密跌停，兆易创新和德明利同样跌停，说明海外冲击已与A股内部高拥挤筹码集中释放共振。今早日经高开0.59%后涨幅回落至0.11%，KOSPI高开1.09%后早盘涨2.19%，均只修复昨日跌幅的一小部分。海外止跌提供边际缓冲，但尚不足以确认科技链风险反转。",
      "assets": [
        "603986",
        "001309",
        "300308",
        "002384",
        "600667",
        "000636"
      ],
      "validation": [
        "跟踪标的开盘后不再批量触及跌停，并相对半导体、CPO或PCB指数止跌",
        "日韩芯片权重守住开盘价，午前反弹幅度不再明显收窄"
      ],
      "invalidation": [
        "A股科技链继续放量下跌并出现新的批量跌停",
        "日经、KOSPI重新跌破前收，三星电子、SK海力士等权重再度加速下探"
      ],
      "urls": [
        "https://finance.cnr.cn/gundong/20260728/t20260728_527734260.shtml",
        "https://indexes.nikkei.co.jp/en/nkave/index/profile",
        "https://www.wsj.com/market-data/quotes/index/KR/SEU/historical-prices"
      ]
    },
    {
      "event": "兆易创新连续跌停，长鑫纳入MSCI令资金与估值替代效应延续",
      "industry": "semi",
      "industry_name": "存储芯片",
      "direction": "negative",
      "strength": 5,
      "horizon": "1-5d",
      "priced_in": "medium",
      "reason": "兆易创新7月28日再次跌停至390.63元，德明利同步跌停；长鑫科技上市次日虽回落约4%，但其首日形成的高估值基准和直接交易载体仍在重塑国产存储资金分配。MSCI宣布长鑫将于8月10日纳入中国全股票指数，可能进一步增加被动及基准资金关注。兆易对长鑫的持股收益不等于自身NOR Flash、MCU和DRAM主营利润同步增长，因此估值拆分仍未结束。",
      "assets": [
        "603986",
        "001309",
        "600667"
      ],
      "validation": [
        "兆易创新打开跌停并相对存储指数企稳，德明利与太极实业不再同步恶化",
        "长鑫成交缩量趋稳，资金不再持续从原有存储映射标的流出"
      ],
      "invalidation": [
        "兆易创新继续封死跌停，存储链出现第三轮批量补跌",
        "长鑫指数纳入预期继续强化资金虹吸，而原有标的缺少经营数据支撑"
      ],
      "urls": [
        "https://finance.sina.cn/2026-07-28/detail-inikimep0430944.d.html",
        "https://finance.sina.com.cn/wm/2026-07-28/doc-inikksxz1835153.shtml",
        "https://www.reuters.com/world/asia-pacific/china-memory-chipmaker-cxmt-set-shanghai-debut-after-asias-biggest-ipo-2026-07-26/"
      ]
    },
    {
      "event": "AI资本开支继续上修，但市场焦点转向融资、供电与投资回报约束",
      "industry": "ai",
      "industry_name": "AI基础设施",
      "direction": "mixed",
      "strength": 4,
      "horizon": "1-5d",
      "priced_in": "low",
      "reason": "Alphabet将2026年资本开支指引上沿由此前约1900亿美元提高至2050亿美元，继续验证数据中心、光模块和PCB需求；同时，美股芯片指数再跌4.5%，市场开始更集中评估AI数据中心的债务融资、供电瓶颈与现金回报。对中际旭创、东山精密而言，需求总量仍有支撑，但短期估值需要微软、Meta等财报中的订单、云收入和资本开支质量确认。",
      "assets": [
        "300308",
        "002384"
      ],
      "validation": [
        "微软、Meta财报确认云收入与AI资本开支同步增长，且未明显下修后续投入",
        "中际旭创、东山精密相对CPO与PCB指数止跌，利好不再伴随冲高回落"
      ],
      "invalidation": [
        "大型云厂商下修资本开支、延迟数据中心项目或强调融资与供电限制",
        "费城半导体继续大跌并引发A股AI硬件新一轮批量抛售"
      ],
      "urls": [
        "https://www.theverge.com/ai-artificial-intelligence/972119/ai-stock-fall-google-capex",
        "https://techcrunch.com/2026/07/28/data-centers-may-face-temporary-power-cuts-on-the-largest-u-s-grid",
        "https://www.reuters.com/business/nasdaq-futures-drop-ai-chip-worries-ahead-pivotal-earnings-2026-07-28/"
      ]
    }
  ]
};
