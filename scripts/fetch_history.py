#!/usr/bin/env python3
"""Refresh daily OHLCV/amount history for the public watchlist.

Eastmoney via AKShare is primary for A-shares, ETFs and LOFs. Yahoo daily chart
is a dependency-free fallback. Failed refreshes preserve prior history as stale.
"""

import json
import math
import os
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCHLIST = os.path.join(ROOT, "watchlist.json")
OUTPUT = os.path.join(ROOT, "market_history.json")
BEIJING = timezone(timedelta(hours=8))
BENCHMARK = {"code": "510300", "name": "沪深300ETF华泰柏瑞", "symbol": "510300.SS", "kind": "etf"}
MAX_ROWS = 140


def load(path):
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


def symbol_for(code):
    suffix = "SS" if str(code).startswith(("5", "6", "9")) else "SZ"
    return f"{code}.{suffix}"


def kind_for(code):
    code = str(code)
    if code.startswith("16"):
        return "lof"
    if code.startswith(("15", "5")):
        return "etf"
    return "stock"


def fresh(last_date, today=None):
    today = today or datetime.now(BEIJING).date()
    try:
        observed = date.fromisoformat(str(last_date)[:10])
    except ValueError:
        return "stale"
    return "fresh" if (today - observed).days <= 4 else "stale"


def frame_rows(frame):
    if frame is None or getattr(frame, "empty", True):
        return []
    rows = []
    for _, source in frame.iterrows():
        values = source.to_dict()
        close = finite(values.get("收盘", values.get("close")))
        raw_date = values.get("日期", values.get("date"))
        if close is None or raw_date is None:
            continue
        rows.append({
            "date": str(raw_date)[:10],
            "open": finite(values.get("开盘", values.get("open"))),
            "high": finite(values.get("最高", values.get("high"))),
            "low": finite(values.get("最低", values.get("low"))),
            "close": close,
            "volume": finite(values.get("成交量", values.get("volume"))),
            "amount": finite(values.get("成交额", values.get("amount"))),
        })
    rows.sort(key=lambda row: row["date"])
    return rows[-MAX_ROWS:]


def akshare_history(code, kind, now=None):
    import akshare as ak

    now = now or datetime.now(BEIJING)
    start = (now.date() - timedelta(days=420)).strftime("%Y%m%d")
    end = now.date().strftime("%Y%m%d")
    if kind == "lof":
        frame = ak.fund_lof_hist_em(symbol=str(code), period="daily", start_date=start, end_date=end, adjust="")
    elif kind == "etf":
        frame = ak.fund_etf_hist_em(symbol=str(code), period="daily", start_date=start, end_date=end, adjust="")
    else:
        frame = ak.stock_zh_a_hist(symbol=str(code), period="daily", start_date=start, end_date=end, adjust="", timeout=20)
    rows = frame_rows(frame)
    if len(rows) < 20:
        raise RuntimeError(f"AKShare returned too few rows for {code}: {len(rows)}")
    return rows


def yahoo_chart(symbol):
    endpoint = "https://query1.finance.yahoo.com/v8/finance/chart/"
    url = endpoint + urllib.parse.quote(symbol) + "?range=1y&interval=1d"
    request = urllib.request.Request(url, headers={"User-Agent": "investment-news/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = (payload.get("chart", {}).get("result") or [None])[0]
    if not result:
        raise RuntimeError(f"no Yahoo chart result for {symbol}")
    timestamps = result.get("timestamp") or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    fields = {name: quote.get(name) or [] for name in ("open", "high", "low", "close", "volume")}
    rows = []
    for i, ts in enumerate(timestamps):
        close = finite(fields["close"][i]) if i < len(fields["close"]) else None
        if close is None:
            continue
        rows.append({
            "date": datetime.fromtimestamp(ts, BEIJING).date().isoformat(),
            "open": finite(fields["open"][i]) if i < len(fields["open"]) else None,
            "high": finite(fields["high"][i]) if i < len(fields["high"]) else None,
            "low": finite(fields["low"][i]) if i < len(fields["low"]) else None,
            "close": close,
            "volume": finite(fields["volume"][i]) if i < len(fields["volume"]) else None,
            "amount": None,
        })
    if len(rows) < 20:
        raise RuntimeError(f"Yahoo returned too few rows for {symbol}: {len(rows)}")
    return rows[-MAX_ROWS:]


def series(code, name, symbol, kind, rows, source, error=None):
    last_date = rows[-1]["date"] if rows else None
    payload = {
        "code": str(code), "name": name, "symbol": symbol, "kind": kind,
        "status": fresh(last_date), "source": source,
        "last_date": last_date, "observations": len(rows), "rows": rows,
    }
    if error:
        payload["error"] = str(error)[:240]
    return payload


def preserve(previous, code, name, symbol, kind, error, benchmark=False):
    old = previous.get("benchmark") if benchmark else previous.get("assets", {}).get(str(code))
    if old and old.get("rows"):
        kept = dict(old)
        kept["status"] = "stale"
        kept["error"] = str(error)[:240]
        return kept
    return series(code, name, symbol, kind, [], "unavailable", error)


def refresh(code, name, symbol, kind, previous, warnings, benchmark=False):
    try:
        rows = akshare_history(code, kind)
        return series(code, name, symbol, kind, rows, "东方财富 via AKShare")
    except Exception as primary:
        warnings.append(f"{code} AKShare: {primary}")
        try:
            rows = yahoo_chart(symbol)
            return series(code, name, symbol, kind, rows, "Yahoo Finance chart", primary)
        except Exception as fallback:
            warnings.append(f"{code} Yahoo: {fallback}")
            return preserve(previous, code, name, symbol, kind, f"AKShare={primary}; Yahoo={fallback}", benchmark)


def main():
    watchlist = load(WATCHLIST)
    previous = load(OUTPUT)
    warnings = []
    benchmark = refresh(
        BENCHMARK["code"], BENCHMARK["name"], BENCHMARK["symbol"], BENCHMARK["kind"],
        previous, warnings, benchmark=True,
    )

    assets = {}
    for asset in watchlist.get("assets", []):
        code = str(asset["code"])
        assets[code] = refresh(code, asset["name"], symbol_for(code), kind_for(code), previous, warnings)

    fresh_count = sum(row.get("status") == "fresh" for row in assets.values())
    stale_count = sum(row.get("status") == "stale" for row in assets.values())
    payload = {
        "version": 2,
        "generated_at": datetime.now(BEIJING).isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "benchmark": benchmark,
        "summary": {"total": len(assets), "fresh": fresh_count, "stale": stale_count, "unavailable": len(assets) - fresh_count - stale_count},
        "assets": assets,
        "warnings": warnings,
        "methodology": "Eastmoney via AKShare is primary for stock/ETF/LOF daily history; Yahoo chart is fallback; prior valid series is retained as stale on total failure; up to 140 observations retained.",
    }
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("history", payload["summary"], "benchmark", benchmark.get("status"), "warnings", len(warnings))


if __name__ == "__main__":
    main()
