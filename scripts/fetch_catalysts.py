#!/usr/bin/env python3
"""Build a public upcoming catalyst calendar for tracked assets.

A-share earnings appointments are fetched from AKShare/Eastmoney. A small manual
overlay can add macro/product/FDA/overseas events that are not available from a
single structured public endpoint. Missing future-event data is left missing,
never fabricated.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "catalysts.json")
WATCHLIST = os.path.join(ROOT, "watchlist.json")
MANUAL = os.path.join(ROOT, "catalysts_manual.json")
BEIJING = timezone(timedelta(hours=8))


def load_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def report_period(today):
    year = today.year
    if today.month <= 3:
        return f"{year-1}1231", f"{year-1}年报"
    if today.month <= 5:
        return f"{year}0331", f"{year}一季报"
    if today.month <= 9:
        return f"{year}0630", f"{year}半年报"
    if today.month <= 11:
        return f"{year}0930", f"{year}三季报"
    return f"{year}1231", f"{year}年报"


def normalize_date(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "nat", "none", "-"}:
        return None
    text = text[:10].replace("/", "-")
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        return None


def latest_appointment(row):
    for key in ("三次变更日期", "二次变更日期", "一次变更日期", "首次预约时间", "首次预约"):
        value = normalize_date(row.get(key))
        if value:
            return value
    return None


def stock_codes(watchlist):
    output = set()
    for asset in watchlist.get("assets", []):
        code = str(asset.get("code", ""))
        if code.startswith(("000", "001", "002", "003", "300", "301", "600", "601", "603", "605", "688")):
            output.add(code)
    return output


def fetch_earnings(watchlist, today=None):
    import akshare as ak

    today = today or datetime.now(BEIJING).date()
    period_code, period_label = report_period(today)
    tracked = stock_codes(watchlist)
    events = []
    warnings = []
    frame = None
    try:
        frame = ak.stock_yysj_em(symbol="沪深A股", date=period_code)
    except Exception as exc:
        warnings.append(f"stock_yysj_em {period_code}: {exc}")
    if frame is None or getattr(frame, "empty", True):
        return events, warnings, period_label
    horizon = today + timedelta(days=45)
    for _, series in frame.iterrows():
        row = series.to_dict()
        code = str(row.get("股票代码", row.get("代码", ""))).strip().zfill(6)
        if code not in tracked:
            continue
        event_date = latest_appointment(row)
        if not event_date:
            continue
        observed = date.fromisoformat(event_date)
        if observed < today - timedelta(days=1) or observed > horizon:
            continue
        name = str(row.get("股票简称", row.get("简称", code))).strip()
        events.append({
            "date": event_date,
            "type": "earnings",
            "title": f"{name} {period_label}预约披露",
            "assets": [code],
            "name": name,
            "source": "东方财富 via AKShare",
            "status": "scheduled",
            "importance": "high" if code in {"603986", "001309", "300308"} else "medium",
        })
    return events, warnings, period_label


def manual_events(today=None):
    today = today or datetime.now(BEIJING).date()
    horizon = today + timedelta(days=45)
    output = []
    for event in load_json(MANUAL).get("events", []):
        event_date = normalize_date(event.get("date"))
        if not event_date:
            continue
        observed = date.fromisoformat(event_date)
        if observed < today - timedelta(days=1) or observed > horizon:
            continue
        item = dict(event)
        item["date"] = event_date
        item.setdefault("type", "manual")
        item.setdefault("status", "scheduled")
        item.setdefault("importance", "medium")
        item.setdefault("source", "manual public catalyst overlay")
        item.setdefault("assets", [])
        output.append(item)
    return output


def build(watchlist, previous=None, today=None, fetcher=fetch_earnings):
    today = today or datetime.now(BEIJING).date()
    previous = previous or {}
    try:
        earnings, warnings, period_label = fetcher(watchlist, today=today)
    except Exception as exc:
        earnings, warnings, period_label = [], [f"earnings fetch: {exc}"], None
    events = earnings + manual_events(today=today)
    seen, deduped = set(), []
    for event in sorted(events, key=lambda x: (x.get("date", "9999-12-31"), x.get("title", ""))):
        identity = (event.get("date"), event.get("type"), event.get("title"))
        if identity in seen:
            continue
        seen.add(identity)
        deduped.append(event)
    if not deduped and previous.get("events"):
        kept = []
        for old in previous.get("events", []):
            event_date = normalize_date(old.get("date"))
            if event_date and date.fromisoformat(event_date) >= today - timedelta(days=1):
                item = dict(old)
                item["status"] = "stale"
                kept.append(item)
        if kept:
            deduped = kept
            warnings.append("refresh returned no events; preserved prior future events as stale")
    return {
        "version": 1,
        "generated_at": datetime.now(BEIJING).isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "report_period": period_label,
        "events": deduped,
        "summary": {
            "total": len(deduped),
            "earnings": sum(event.get("type") == "earnings" for event in deduped),
            "manual": sum(event.get("type") != "earnings" for event in deduped),
        },
        "warnings": warnings,
        "methodology": "A股财报预约披露来自东方财富/AKShare；其他未来催化来自可审计的手工公共事件覆盖。无数据时不推断具体日期。",
    }


def main():
    watchlist = load_json(WATCHLIST)
    payload = build(watchlist, previous=load_json(OUTPUT))
    tmp = OUTPUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(tmp, OUTPUT)
    print("catalysts", payload["summary"])
    for warning in payload["warnings"]:
        print("warning:", warning)


if __name__ == "__main__":
    main()
