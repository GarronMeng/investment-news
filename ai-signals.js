// 由 ChatGPT 网页版生成；新闻抓取工作流不会覆盖本文件。
window.AI_SIGNALS = {
  "generated_at": "2026-08-04 09:16",
  "source_generated_at": "2026-08-04 09:00",
  "generated_by": "ChatGPT Web",
  "status": "ready",
  "news_titles": {
    "https://www.digitimes.com/news/a20260804PD205/cxmt-dram-market-competition-capacity-expansion.html": "长鑫上市引发对DRAM价格及全球存储竞争的担忧",
    "https://semiengineering.com/nad-memory-combines-nand-flash-and-dram-for-faster-data-transfer-u-of-seoul": "首尔大学研发混合存储器，结合NAND与DRAM提升传输速度",
    "https://www.digitimes.com/news/a20260804PR201/sk-hynix-technology-flash-ai-inference-bandwidth.html": "闪迪与SK海力士发布HBF规范，推进AI存储标准",
    "https://www.eetimes.com/renesas-tackles-memory-bottleneck-with-mrdimm-update": "瑞萨升级MRDIMM方案，应对内存带宽瓶颈",
    "https://www.statnews.com/2026/08/03/biotech-news-is-there-a-pharma-mega-merger-coming-astrazeneca-bms": "阿斯利康与百时美施贵宝会否酝酿医药巨头并购",
    "https://www.eetimes.com/cea-leti-pushes-stacking-roadmap-as-ai-runs-into-memory-and-power-limits": "CEA-Leti推进堆叠技术路线，应对AI内存与功耗瓶颈"
  },
  "overseas_markets": [
    {
      "market": "美股",
      "flag": "🇺🇸",
      "session": "8月3日收盘",
      "updated_at": "2026-08-04 09:16 CST",
      "status": "positive",
      "status_label": "伊朗谈判与AI盈利预期推动风险偏好修复",
      "move": "标普500 +1.48%｜道指 +1.32%｜纳指 +2.13%",
      "driver": "美股三大指数齐升，道指创收盘新高；Amazon上涨约4.6%，Microsoft、Meta、Alphabet等AI及云计算权重同步走强。原油结算价下跌约5%缓和短期通胀压力，但市场对9月加息的隐含概率仍约65%，利率约束并未消失。",
      "a_share_links": ["CPO", "PCB", "AI服务器", "存储芯片"],
      "validation": "A股开盘后观察中际旭创、东山精密能否停止相对弱势并获得成交承接；若继续弱于通信、电子指数，则海外利好尚未完成国内价格传导。",
      "sources": [
        "https://www.reuters.com/business/wall-st-futures-edge-up-mideast-deal-hopes-healthcare-focus-2026-08-03/",
        "https://www.reuters.com/legal/transactional/amazon-enters-3-trillion-club-ai-optimism-sweeps-through-wall-street-2026-08-03/"
      ]
    },
    {
      "market": "日股",
      "flag": "🇯🇵",
      "session": "8月4日早盘",
      "updated_at": "2026-08-04 09:16 CST",
      "status": "pending",
      "status_label": "开盘数据单源，冲高回落方向待复核",
      "move": "开盘63,995.28（较前收高0.38%）｜09:48 JST报63,241.80，跌0.80%",
      "driver": "日经225前收63,754.90，今早小幅高开；早段芯片股一度带动指数上涨，但随后转跌。Reuters在另一观测时点记录日经跌约0.3%，与回落方向一致；因未取得第二个独立来源的精确开盘点位，按规则保留待验证状态。",
      "a_share_links": ["半导体设备", "被动元件", "消费电子", "AI硬件"],
      "validation": "继续核对日经官方开盘数据，并观察指数能否收复开盘价；A股重点看风华高科、东山精密能否形成独立强弱。",
      "sources": [
        "https://www.wsj.com/market-data/quotes/index/JP/NIK",
        "https://www.reuters.com/world/china/global-markets-wrapup-1-2026-08-04/",
        "https://www.wsj.com/finance/stocks/nikkei-rises-0-4-led-by-chip-stocks-e1d183bc"
      ]
    },
    {
      "market": "韩股",
      "flag": "🇰🇷",
      "session": "8月4日早盘",
      "updated_at": "2026-08-04 09:16 CST",
      "status": "pending",
      "status_label": "开盘数据单源，反弹持续性待复核",
      "move": "开盘6,351.38（较前收高1.50%）｜09:23 KST报6,294.56，涨0.59%",
      "driver": "KOSPI前收6,257.45，今早高开后涨幅收窄；Reuters在另一时点记录指数一度上涨2.1%，方向一致但观测时间不同。该反弹发生在8月3日收跌5.12%之后，仍属于高波动修复；因精确开盘点位缺少第二来源，继续标记待验证。",
      "a_share_links": ["DRAM", "NAND", "HBM", "封测"],
      "validation": "核对KRX开盘与收盘数据，观察三星电子、SK海力士及KOSPI能否守住前收；A股对应关注兆易创新、德明利、太极实业是否停止补跌。",
      "sources": [
        "https://www.wsj.com/market-data/quotes/index/KR/SEU",
        "https://www.reuters.com/world/china/global-markets-wrapup-1-2026-08-04/",
        "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=en"
      ]
    }
  ],
  "signals": [
    {
      "event": "存储原厂据报2027年产能提前分配、HBF规范推进，但A股存储链价格验证仍为负面",
      "industry": "semi",
      "industry_name": "DRAM / NAND / AI存储",
      "direction": "mixed",
      "strength": 5,
      "horizon": "1-4w",
      "priced_in": "unknown",
      "reason": "产业媒体报道称三星、Micron、SK海力士的2027年DRAM与HBM产能已提前分配，部分NAND原厂产能也趋紧；Sandisk与SK海力士同时发布HBF规范，推进面向AI推理的高带宽闪存标准。需求和供需信息偏正面，但8月3日兆易创新跌停、德明利跌9.56%、太极实业跌5.51%，回购与需求利好均未获得A股价格确认。产能分配目前主要来自产业媒体，仍需原厂订单、报价或正式文件交叉验证。",
      "assets": ["603986", "001309", "600667"],
      "validation": [
        "原厂正式披露2027年订单覆盖、价格或资本开支指引，DRAM与NAND现货及合约价继续上行",
        "兆易创新、德明利、太极实业停止弱于半导体指数，且放量收复8月3日主要跌幅"
      ],
      "invalidation": [
        "原厂否认产能售罄报道，或后续价格、库存数据不支持供需趋紧",
        "相关标的继续放量创新低，显示产业利好仍不足以抵消估值与筹码压力"
      ],
      "urls": [
        "https://wallstreetcn.com/articles/3778618",
        "https://www.digitimes.com/news/a20260804PR201/sk-hynix-technology-flash-ai-inference-bandwidth.html",
        "https://www.stcn.com/article/detail/4055434.html"
      ]
    },
    {
      "event": "美国AI与云计算权重反弹，但A股CPO和PCB仍需完成独立价格确认",
      "industry": "ai",
      "industry_name": "AI数据中心 / CPO / PCB",
      "direction": "mixed",
      "strength": 4,
      "horizon": "1-5d",
      "priced_in": "medium",
      "reason": "Amazon因AWS增速与AI投资预期上涨约4.6%，Microsoft、Meta、Alphabet同步走强，纳指上涨2.13%，继续支持数据中心、光模块和服务器PCB需求预期。与此同时，8月3日东山精密下跌5.06%，A股电子板块下跌4.18%，说明海外需求逻辑尚未转化为国内稳定价格趋势；中际旭创的实时A/H反馈盘前仍待验证。",
      "assets": ["300308", "002384"],
      "validation": [
        "中际旭创、东山精密开盘后相对通信和电子指数转强，并减少冲高回落",
        "后续云厂商资本开支、交换机和光模块订单继续确认需求兑现"
      ],
      "invalidation": [
        "A股CPO、PCB继续放量补跌并弱于板块，海外上涨未形成国内承接",
        "云厂商下调资本开支或现金流压力导致AI基础设施投资延后"
      ],
      "urls": [
        "https://www.reuters.com/business/wall-st-futures-edge-up-mideast-deal-hopes-healthcare-focus-2026-08-03/",
        "https://www.reuters.com/legal/transactional/amazon-enters-3-trillion-club-ai-optimism-sweeps-through-wall-street-2026-08-03/",
        "https://www.stcn.com/article/detail/4055434.html"
      ]
    },
    {
      "event": "风华高科逆电子板块上涨，MLCC涨价首次获得相对价格确认",
      "industry": "components",
      "industry_name": "被动元件 / MLCC",
      "direction": "positive",
      "strength": 4,
      "horizon": "1-4w",
      "priced_in": "medium",
      "reason": "三星电机自8月1日起执行MLCC调价、太阳诱电计划9月调价。8月3日电子板块下跌4.18%的同时，风华高科上涨5.29%，并获得特大单口径净流入，说明涨价催化首次得到A股相对价格确认；但今早日经冲高回落、海外电子链并未一致转强，实际渠道成交价、订单和下游接受度仍是基本面验证条件。",
      "assets": ["000636"],
      "validation": [
        "渠道和公司订单显示高容值、高可靠MLCC成交价与出货量同步改善",
        "风华高科持续强于被动元件和电子指数，且高换手逐步下降"
      ],
      "invalidation": [
        "下游抵制涨价、削减订单或实际成交价未跟随通知",
        "风华高科快速跌回涨价催化前区间，8月3日相对强势被完全回吐"
      ],
      "urls": [
        "https://www.cls.cn/detail/2441445",
        "https://www.stcn.com/article/detail/4055434.html",
        "https://www.wsj.com/market-data/quotes/index/JP/NIK"
      ]
    }
  ]
};
