#!/usr/bin/env python3
"""Refresh daily OHLCV history for the public watchlist."""

import json
import os
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCHLIST = os.path.join(ROOT, "watchlist.json")
OUTPUT = os.path.join(ROOT, "market_history.json")
BEIJING = timezone(timedelta(hours=8))
BENCHMARK = {"code": "000300", "name": "沪深300", "symbol": "000300.SS"}
MAX_ROWS = 140


def load(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def symbol_for(code):
    suffix = "SS" if str(code).startswith(("5", "6", "9")) else "SZ"
    return f"{code}.{suffix}"


def fresh(last_date, today=None):
    today = today or datetime.now(BEIJING).date()
    try:
        observed = date.fromisoformat(str(last_date)[:10])
    except ValueError:
        return "stale"
    return "fresh" if (today - observed).days <= 4 else "stale"


def chart(symbol):
    endpoint = "https://query1.finance.yahoo.com/v8/finance/chart/"
    url = endpoint + urllib.parse.quote(symbol) + "?range=1y&interval=1d"
    request = urllib.request.Request(url, headers={"User-Agent": "investment-news/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = (payload.get("chart", {}).get("result") or [None])[0]
    if not result:
        raise RuntimeError(f"no chart result for {symbol}")
    timestamps = result.get("timestamp") or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    fields = {name: quote.get(name) or [] for name in ("open", "high", "low", "close", "volume")}
    rows = []
    for i, ts in enumerate(timestamps):
        close = fields["close"][i] if i < len(fields["close"]) else None
        if close is None:
            continue
        row = {"date": datetime.fromtimestamp(ts, BEIJING).date().isoformat()}
        for name in fields:
            row[name] = fields[name][i] if i < len(fields[name]) else None
        rows.append(row)
    if len(rows) < 20:
        raise RuntimeError(f"too few rows for {symbol}: {len(rows)}")
    return rows[-MAX_ROWS:]


def item(code, name, symbol, rows, error=None):
    last_date = rows[-1]["date"] if rows else None
    payload = {
        "code": str(code), "name": name, "symbol": symbol,
        "status": fresh(last_date), "source": "Yahoo Finance chart",
        "last_date": last_date, "observations": len(rows), "rows": rows,
    }
    if error:
        payload["error"] = str(error)[:240]
    return payload


def previous_or_empty(previous, code, name, symbol, error, benchmark=False):
    old = previous.get("benchmark") if benchmark else previous.get("assets", {}).get(str(code))
    if old and old.get("rows"):
        kept = dict(old)
        kept["status"] = "stale"
        kept["error"] = str(error)[:240]
        return kept
    return item(code, name, symbol, [], error)


def main():
    watchlist = load(WATCHLIST)
    previous = load(OUTPUT)
    warnings = []
    try:
        benchmark = item(BENCHMARK["code"], BENCHMARK["name"], BENCHMARK["symbol"], chart(BENCHMARK["symbol"]))
    except Exception as exc:
        warnings.append(f"benchmark: {exc}")
        benchmark = previous_or_empty(previous, BENCHMARK["code"], BENCHMARK["name"], BENCHMARK["symbol"], exc, True)

    assets = {}
    for asset in watchlist.get("assets", []):
        code = str(asset["code"])
        symbol = symbol_for(code)
        try:
            assets[code] = item(code, asset["name"], symbol, chart(symbol))
        except Exception as exc:
            warnings.append(f"{code}: {exc}")
            assets[code] = previous_or_empty(previous, code, asset["name"], symbol, exc)

    fresh_count = sum(row.get("status") == "fresh" for row in assets.values())
    stale_count = sum(row.get("status") == "stale" for row in assets.values())
    payload = {
        "version": 1,
        "generated_at": datetime.now(BEIJING).isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "benchmark": benchmark,
        "summary": {"total": len(assets), "fresh": fresh_count, "stale": stale_count, "unavailable": len(assets) - fresh_count - stale_count},
        "assets": assets,
        "warnings": warnings,
        "methodology": "Daily Yahoo chart history; keep prior valid series as stale when refresh fails; retain up to 140 observations.",
    }
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("history", payload["summary"], "warnings", len(warnings))


if __name__ == "__main__":
    main()
