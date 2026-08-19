#!/usr/bin/env python3
"""Fetch a compact cross-asset snapshot for Daily Flash.

Uses Yahoo Finance chart endpoints already employed elsewhere in this repository.
Missing observations are preserved as stale/unavailable; they are never filled
with zero. Output is descriptive market data only.
"""

from __future__ import annotations

import json
import math
import os
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "global_markets.json")
BEIJING = timezone(timedelta(hours=8))

ASSETS = [
    {"key": "sp500", "name": "标普500", "symbol": "^GSPC", "group": "美股", "unit": "index"},
    {"key": "nasdaq", "name": "纳斯达克", "symbol": "^IXIC", "group": "美股", "unit": "index"},
    {"key": "sox", "name": "费城半导体", "symbol": "^SOX", "group": "美股", "unit": "index"},
    {"key": "hsi", "name": "恒生指数", "symbol": "^HSI", "group": "港股", "unit": "index"},
    {"key": "nikkei", "name": "日经225", "symbol": "^N225", "group": "亚洲", "unit": "index"},
    {"key": "kospi", "name": "韩国综合", "symbol": "^KS11", "group": "亚洲", "unit": "index"},
    {"key": "vix", "name": "VIX", "symbol": "^VIX", "group": "风险", "unit": "index"},
    {"key": "us10y", "name": "美债10Y", "symbol": "^TNX", "group": "利率", "unit": "yield"},
    {"key": "dxy", "name": "美元指数", "symbol": "DX-Y.NYB", "group": "汇率", "unit": "index"},
    {"key": "usdcnh", "name": "USD/CNH", "symbol": "CNH=X", "group": "汇率", "unit": "fx"},
    {"key": "gold", "name": "黄金", "symbol": "GC=F", "group": "商品", "unit": "usd"},
    {"key": "silver", "name": "白银", "symbol": "SI=F", "group": "商品", "unit": "usd"},
    {"key": "wti", "name": "WTI原油", "symbol": "CL=F", "group": "商品", "unit": "usd"},
    {"key": "brent", "name": "布伦特原油", "symbol": "BZ=F", "group": "商品", "unit": "usd"},
]


def finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def status_for(as_of, today=None):
    today = today or datetime.now(BEIJING).date()
    try:
        observed = date.fromisoformat(str(as_of)[:10])
    except (TypeError, ValueError):
        return "stale"
    return "fresh" if (today - observed).days <= 4 else "stale"


def yahoo_chart(asset):
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + urllib.parse.quote(asset["symbol"])
        + "?range=5d&interval=1d"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "investment-news/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = payload["chart"]["result"][0]
    timestamps = result.get("timestamp") or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []
    valid = [(ts, finite(value)) for ts, value in zip(timestamps, closes) if finite(value) is not None]
    if not valid:
        raise ValueError(f"Yahoo returned no close for {asset['symbol']}")
    observed_ts, price = valid[-1]
    previous = valid[-2][1] if len(valid) >= 2 else None
    observed = datetime.fromtimestamp(observed_ts, BEIJING).isoformat(timespec="seconds")
    change_pct = (price / previous - 1) * 100 if previous not in (None, 0) else None
    display_value = price
    if asset["unit"] == "yield" and price is not None and price > 20:
        display_value = price / 10.0
    return {
        "key": asset["key"],
        "name": asset["name"],
        "symbol": asset["symbol"],
        "group": asset["group"],
        "unit": asset["unit"],
        "value": round(display_value, 4) if display_value is not None else None,
        "raw_value": round(price, 4) if price is not None else None,
        "previous_close": round(previous, 4) if previous is not None else None,
        "change_pct": round(change_pct, 2) if change_pct is not None else None,
        "as_of": observed,
        "status": status_for(observed),
        "source": "Yahoo Finance",
    }


def load_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def preserve(previous, asset, error):
    old = next((row for row in previous.get("assets", []) if row.get("key") == asset["key"]), None)
    if old and old.get("value") is not None:
        kept = dict(old)
        kept["status"] = "stale"
        kept["error"] = str(error)[:200]
        return kept
    return {
        "key": asset["key"], "name": asset["name"], "symbol": asset["symbol"],
        "group": asset["group"], "unit": asset["unit"], "value": None,
        "raw_value": None, "previous_close": None, "change_pct": None,
        "as_of": None, "status": "unavailable", "source": "行情源待恢复",
        "error": str(error)[:200],
    }


def build(previous=None, now=None, fetcher=yahoo_chart):
    previous = previous or {}
    now = now or datetime.now(BEIJING)
    rows, warnings = [], []
    for asset in ASSETS:
        try:
            rows.append(fetcher(asset))
        except Exception as exc:
            warnings.append(f"{asset['key']}: {exc}")
            rows.append(preserve(previous, asset, exc))
    fresh = sum(row.get("status") == "fresh" for row in rows)
    stale = sum(row.get("status") == "stale" for row in rows)
    return {
        "version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "summary": {"total": len(rows), "fresh": fresh, "stale": stale, "unavailable": len(rows) - fresh - stale},
        "assets": rows,
        "warnings": warnings,
        "methodology": "Yahoo Finance日线跨资产快照；失败保留最近成功值并显式标记stale/unavailable。美债10Y的^TNX展示值按Yahoo指数惯例换算为收益率百分比。",
    }


def main():
    payload = build(previous=load_json(OUTPUT))
    tmp = OUTPUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(tmp, OUTPUT)
    print("global markets", payload["summary"])
    for warning in payload["warnings"]:
        print("warning:", warning)


if __name__ == "__main__":
    main()
