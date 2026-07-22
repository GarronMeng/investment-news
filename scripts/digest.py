#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将行业新闻转换为 A 股信号：事件、标的映射、方向、强度、周期、验证与失效条件。"""
import json
import os
from concurrent.futures import ThreadPoolExecutor
import llm

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOPN = 18
WORKERS = 3
ATTEMPTS = 2
CFG = {"provider": "api"}
WATCHLIST = {}

SYS = """你是严谨的A股产业链研究助手。输入包含一个行业的近期新闻与用户关注标的。
你的任务不是给出买卖建议，而是识别可验证的产业事件及其A股映射。
只输出JSON，禁止输出解释或代码块。要求：
1. 将重复报道合并为最多4个signals。
2. 每个signal字段：event（不超过45字）、direction（positive/negative/mixed/neutral）、strength（1-5整数）、horizon（intraday/1-5d/1-4w/1-3m）、priced_in（unknown/low/medium/high）、reason（不超过60字）、assets（关注标的代码数组）、validation（最多2条市场验证条件）、invalidation（最多2条失效条件）、refs（新闻序号数组）。
3. 只有存在明确逻辑链时才映射标的；无映射则assets为空。
4. 无行情数据时priced_in优先用unknown，并在validation中要求价格、成交量或板块联动确认。
5. 同时返回items，每条新闻给出简洁中文标题。
格式：{"signals":[{"event":"...","direction":"positive","strength":4,"horizon":"1-5d","priced_in":"unknown","reason":"...","assets":["603986"],"validation":["..."],"invalidation":["..."],"refs":[0,2]}],"items":[{"i":0,"zh":"..."}]}"""


def extract_json(text):
    if not text:
        return None
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except Exception:
        return None


def asset_context(industry_key):
    assets = []
    for asset in WATCHLIST.get("assets", []):
        if industry_key in asset.get("industries", []):
            assets.append({
                "code": asset["code"],
                "name": asset["name"],
                "priority": asset.get("priority", 1),
                "thesis": asset.get("thesis", ""),
                "keywords": asset.get("keywords", []),
                "positive_triggers": asset.get("positive_triggers", []),
                "negative_triggers": asset.get("negative_triggers", []),
                "market_validation": asset.get("market_validation", [])
            })
    return assets


def call_llm(user, label):
    try:
        return llm.call(SYS, user, CFG, timeout=300)
    except Exception as exc:
        print("  ⚠️ LLM异常[%s]: %s" % (label, str(exc)[:150]))
        return ""


def normalize_signal(raw, items, valid_codes, industry):
    refs = [r for r in raw.get("refs", []) if isinstance(r, int) and 0 <= r < len(items)]
    urls = [items[r].get("url", "") for r in refs if items[r].get("url")]
    direction = raw.get("direction", "neutral")
    if direction not in ("positive", "negative", "mixed", "neutral"):
        direction = "neutral"
    horizon = raw.get("horizon", "1-5d")
    if horizon not in ("intraday", "1-5d", "1-4w", "1-3m"):
        horizon = "1-5d"
    priced_in = raw.get("priced_in", "unknown")
    if priced_in not in ("unknown", "low", "medium", "high"):
        priced_in = "unknown"
    try:
        strength = max(1, min(5, int(raw.get("strength", 1))))
    except Exception:
        strength = 1
    assets = [code for code in raw.get("assets", []) if code in valid_codes]
    event = str(raw.get("event", "")).strip()[:80]
    if not event:
        return None
    return {
        "event": event,
        "industry": industry["key"],
        "industry_name": industry["name"],
        "direction": direction,
        "strength": strength,
        "horizon": horizon,
        "priced_in": priced_in,
        "reason": str(raw.get("reason", "")).strip()[:120],
        "assets": assets,
        "validation": [str(x).strip()[:80] for x in raw.get("validation", []) if str(x).strip()][:2],
        "invalidation": [str(x).strip()[:80] for x in raw.get("invalidation", []) if str(x).strip()][:2],
        "refs": refs,
        "urls": urls[:3]
    }


def process(industry):
    items = industry.get("items", [])[:TOPN]
    industry["items"] = items
    industry["signals"] = []
    if not items:
        return industry

    assets = asset_context(industry["key"])
    valid_codes = {asset["code"] for asset in assets}
    news_lines = []
    for idx, item in enumerate(items):
        news_lines.append("%d. %s | %s | %s" %
                          (idx, item.get("title", ""), item.get("source", ""), item.get("summary", "")))
    user = json.dumps({
        "industry": {"key": industry["key"], "name": industry["name"]},
        "watchlist_assets": assets,
        "news": news_lines
    }, ensure_ascii=False)

    parsed = None
    for _ in range(ATTEMPTS):
        parsed = extract_json(call_llm(user, industry["name"]))
        if parsed:
            break
    if not parsed:
        print("  ⚠️ %s 未生成AI信号，保留原始新闻。" % industry["name"])
        return industry

    translations = {x.get("i"): x.get("zh", "") for x in parsed.get("items", []) if isinstance(x, dict)}
    for idx, item in enumerate(items):
        item["zh"] = str(translations.get(idx, "")).strip()

    signals = []
    for raw in parsed.get("signals", [])[:4]:
        if isinstance(raw, dict):
            signal = normalize_signal(raw, items, valid_codes, industry)
            if signal:
                signals.append(signal)
    industry["signals"] = signals
    industry["points"] = [{"t": s["event"], "url": s["urls"][0] if s["urls"] else ""} for s in signals]
    return industry


def fallback_watchlist(data):
    counts = {}
    for industry in data.get("industries", []):
        corpus = " ".join((item.get("title", "") + " " + item.get("summary", "")).lower()
                          for item in industry.get("items", []))
        for asset in WATCHLIST.get("assets", []):
            hits = sum(1 for keyword in asset.get("keywords", []) if keyword.lower() in corpus)
            if hits:
                counts[asset["code"]] = counts.get(asset["code"], 0) + hits
    output = []
    for asset in WATCHLIST.get("assets", []):
        row = dict(asset)
        row["news_hits"] = counts.get(asset["code"], 0)
        output.append(row)
    return sorted(output, key=lambda x: (-x.get("news_hits", 0), -x.get("priority", 0)))


def main():
    global CFG, WATCHLIST
    CFG = llm.load_config(ROOT)
    WATCHLIST = json.load(open(os.path.join(ROOT, "watchlist.json"), encoding="utf-8"))
    path = os.path.join(ROOT, "data.js")
    text = open(path, encoding="utf-8").read()
    data = json.loads(text[text.index("{"):text.rindex("}") + 1])
    industries = data.get("industries", [])

    provider = CFG.get("provider", "claude-cli")
    print("大模型 provider:", provider)
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        list(executor.map(process, industries))

    signals = []
    for industry in industries:
        signals.extend(industry.get("signals", []))
    priority = {asset["code"]: asset.get("priority", 1) for asset in WATCHLIST.get("assets", [])}
    signals.sort(key=lambda s: (-s["strength"], -max([priority.get(c, 0) for c in s["assets"]] or [0])))
    max_signals = WATCHLIST.get("decision_rules", {}).get("max_dashboard_signals", 12)
    data["signals"] = signals[:max_signals]
    data["watchlist"] = fallback_watchlist(data)
    data["profile"] = WATCHLIST.get("profile", {})
    data["decision_rules"] = WATCHLIST.get("decision_rules", {})
    data["has_ai"] = bool(signals)

    with open(path, "w", encoding="utf-8") as output:
        output.write("// 自动生成，请勿手工编辑。\n")
        output.write("window.DATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
    print("生成 %d 条A股映射信号。" % len(data["signals"]))


if __name__ == "__main__":
    main()
