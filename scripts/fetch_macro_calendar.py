#!/usr/bin/env python3
"""Build a 10-day macro and global earnings catalyst calendar.

Sources are public AKShare/Baidu calendar endpoints. The calendar is descriptive:
importance is inherited from the source, impact channels are deterministic keyword
mappings, and missing dates are never invented. Selected global companies come
from a public research-universe config and do not imply a recommendation.
"""

from __future__ import annotations

import json
import math
import os
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "macro_calendar.json")
UNIVERSE = os.path.join(ROOT, "global_catalyst_universe.json")
BEIJING = timezone(timedelta(hours=8))
HORIZON_DAYS = 10
RELEVANT_REGIONS = {"中国", "美国", "欧元区", "日本", "韩国", "中国香港", "英国"}

THEME_ASSETS = {
    "存储": ["603986", "001309"],
    "AI光通信 / CPO": ["300308"],
    "AI算力": ["300308", "002384", "600667"],
    "半导体": ["603986", "001309", "600667"],
    "创新药": ["517380"],
}


def load_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def normalize_date(value):
    text = str(value or "").strip()[:10].replace("/", "-")
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        return None


def event_category(text):
    text = str(text or "")
    rules = [
        ("monetary_policy", ("利率决议", "央行", "FOMC", "联储", "会议纪要", "利率决定")),
        ("inflation", ("CPI", "PPI", "通胀", "物价")),
        ("labor", ("非农", "失业", "初请", "就业", "ADP")),
        ("growth", ("GDP", "PMI", "零售", "工业产出", "工业增加值", "消费", "耐用品")),
        ("liquidity", ("M2", "社融", "社会融资", "新增人民币贷款", "信贷", "LPR")),
        ("trade", ("贸易帐", "出口", "进口")),
        ("housing", ("房屋", "房地产", "新屋", "成屋")),
        ("energy", ("原油库存", "EIA", "API", "天然气库存")),
    ]
    for category, keys in rules:
        if any(key.lower() in text.lower() for key in keys):
            return category
    return "macro"


def impact_channels(region, category, text):
    channels = []
    if region == "美国":
        if category in {"monetary_policy", "inflation", "labor"}:
            channels.extend(["美债收益率", "美元", "全球成长估值", "黄金/白银"])
        elif category == "growth":
            channels.extend(["全球风险偏好", "AI资本开支预期", "美元"])
        elif category == "energy":
            channels.extend(["原油", "通胀预期", "风险偏好"])
    elif region == "中国":
        if category in {"liquidity", "monetary_policy"}:
            channels.extend(["A股流动性", "人民币汇率", "成长估值"])
        elif category in {"growth", "inflation", "trade"}:
            channels.extend(["中国增长预期", "行业盈利预期", "人民币汇率"])
    elif region in {"日本", "韩国"}:
        channels.extend(["亚洲科技风险偏好", "半导体链映射"])
    elif region == "中国香港":
        channels.extend(["港股风险偏好", "跨境资金"])
    elif region in {"欧元区", "英国"}:
        channels.extend(["全球利率", "美元相对强弱", "风险偏好"])
    if not channels:
        channels.append("宏观环境")
    return list(dict.fromkeys(channels))


def normalize_macro_row(row):
    event_date = normalize_date(row.get("日期"))
    region = str(row.get("地区") or "").strip()
    title = str(row.get("事件") or "").strip()
    importance = finite(row.get("重要性"))
    if not event_date or not title or region not in RELEVANT_REGIONS:
        return None
    if importance is not None and importance < 2:
        return None
    category = event_category(title)
    return {
        "date": event_date,
        "time": str(row.get("时间") or "").strip() or None,
        "type": "macro",
        "category": category,
        "region": region,
        "title": title,
        "actual": finite(row.get("公布")),
        "forecast": finite(row.get("预期")),
        "previous": finite(row.get("前值")),
        "importance": int(importance) if importance is not None else None,
        "impact_channels": impact_channels(region, category, title),
        "themes": [],
        "assets": [],
        "source": "百度股市通 via AKShare",
        "status": "scheduled",
    }


def company_map(universe):
    output = {}
    for item in universe.get("companies", []):
        ticker = str(item.get("ticker") or "").upper().strip()
        if ticker:
            output[ticker] = item
    return output


def normalize_report_row(row, event_date, universe_by_ticker):
    ticker = str(row.get("股票代码") or "").upper().strip()
    if ticker not in universe_by_ticker:
        return None
    conf = universe_by_ticker[ticker]
    themes = list(conf.get("themes") or [])
    assets = []
    for theme in themes:
        assets.extend(THEME_ASSETS.get(theme, []))
    return {
        "date": event_date,
        "time": None,
        "type": "global_earnings",
        "category": "earnings",
        "region": str(row.get("交易所") or conf.get("exchange") or "").strip(),
        "title": f"{conf.get('name') or row.get('股票简称') or ticker} 财报发行",
        "ticker": ticker,
        "report_period": str(row.get("财报期") or "").strip() or None,
        "importance": 3 if ticker in {"NVDA", "MU", "MRVL", "AVGO", "MSFT", "META", "GOOGL", "AMZN"} else 2,
        "impact_channels": ["产业链景气", "海外映射", "风险偏好"],
        "themes": themes,
        "assets": list(dict.fromkeys(assets)),
        "source": "百度股市通 via AKShare",
        "status": "scheduled",
    }


def fetch_calendar(today=None, horizon_days=HORIZON_DAYS):
    import akshare as ak

    today = today or datetime.now(BEIJING).date()
    universe = load_json(UNIVERSE)
    by_ticker = company_map(universe)
    events, warnings = [], []
    macro_success = 0
    report_success = 0
    for offset in range(horizon_days + 1):
        day = today + timedelta(days=offset)
        key = day.strftime("%Y%m%d")
        iso = day.isoformat()
        try:
            frame = ak.news_economic_baidu(date=key)
            macro_success += 1
            if frame is not None and not getattr(frame, "empty", True):
                for _, series in frame.iterrows():
                    item = normalize_macro_row(series.to_dict())
                    if item:
                        events.append(item)
        except Exception as exc:
            warnings.append(f"news_economic_baidu {key}: {exc}")
        try:
            frame = ak.news_report_time_baidu(date=key)
            report_success += 1
            if frame is not None and not getattr(frame, "empty", True):
                for _, series in frame.iterrows():
                    item = normalize_report_row(series.to_dict(), iso, by_ticker)
                    if item:
                        events.append(item)
        except Exception as exc:
            warnings.append(f"news_report_time_baidu {key}: {exc}")
    return events, warnings, macro_success, report_success


def dedupe(events):
    seen, output = set(), []
    for event in sorted(events, key=lambda x: (x.get("date", ""), x.get("time") or "99:99", x.get("type", ""), x.get("title", ""))):
        identity = (event.get("date"), event.get("time"), event.get("type"), event.get("title"), event.get("ticker"))
        if identity in seen:
            continue
        seen.add(identity)
        output.append(event)
    return output


def preserve_previous(previous, today):
    kept = []
    end = today + timedelta(days=HORIZON_DAYS)
    for old in previous.get("events", []):
        event_date = normalize_date(old.get("date"))
        if not event_date:
            continue
        observed = date.fromisoformat(event_date)
        if today <= observed <= end:
            item = dict(old)
            item["status"] = "stale"
            kept.append(item)
    return kept


def build(previous=None, today=None, fetcher=fetch_calendar):
    today = today or datetime.now(BEIJING).date()
    previous = previous or {}
    try:
        events, warnings, macro_success, report_success = fetcher(today=today)
    except Exception as exc:
        events, warnings, macro_success, report_success = [], [f"calendar refresh: {exc}"], 0, 0
    events = dedupe(events)
    if macro_success == 0 and report_success == 0 and previous.get("events"):
        events = preserve_previous(previous, today)
        if events:
            warnings.append("all calendar sources failed; preserved prior future events as stale")
    return {
        "version": 1,
        "generated_at": datetime.now(BEIJING).isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "horizon_days": HORIZON_DAYS,
        "events": events,
        "summary": {
            "total": len(events),
            "macro": sum(e.get("type") == "macro" for e in events),
            "global_earnings": sum(e.get("type") == "global_earnings" for e in events),
            "high_importance": sum((e.get("importance") or 0) >= 3 for e in events),
            "macro_days_ok": macro_success,
            "report_days_ok": report_success,
        },
        "warnings": warnings,
        "methodology": {
            "macro": "百度股市通全球宏观日历 via AKShare；仅保留主要经济体且重要性>=2的事件。",
            "global_earnings": "百度股市通财报发行 via AKShare；仅保留global_catalyst_universe.json中的公开研究公司。",
            "mapping": "impact_channels/themes/assets为显式规则映射，用于说明传导路径，不是交易信号或收益概率。",
        },
        "boundary": "未来事件日期来自公开日历；缺失不推断，研究公司池不代表推荐。",
    }


def main():
    payload = build(previous=load_json(OUTPUT))
    temporary = OUTPUT + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, OUTPUT)
    print("macro calendar", payload["summary"])
    for warning in payload["warnings"]:
        print("warning:", warning)


if __name__ == "__main__":
    main()
