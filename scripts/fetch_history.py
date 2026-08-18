#!/usr/bin/env python3
"""Refresh daily OHLCV/amount history for the public watchlist.

Eastmoney via AKShare is primary. A-shares then use the independent Sina daily
history endpoint before Yahoo; funds use Sina, direct Eastmoney, then Yahoo.
After refresh, every A-share/ETF/LOF series is aligned to the benchmark's last
trading date so a one-session-old series cannot be labelled fresh merely because
it is within a loose calendar-day window.
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


def sina_symbol_for(code):
    prefix = "sh" if str(code).startswith(("5", "6", "9")) else "sz"
    return f"{prefix}{code}"


def kind_for(code):
    code = str(code)
    if code.startswith("16"):
        return "lof"
    if code.startswith(("15", "5")):
        return "etf"
    return "stock"


def fresh(last_date, today=None):
    """Loose calendar freshness used only before benchmark-date alignment."""
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


def date_range(now=None):
    now = now or datetime.now(BEIJING)
    return (now.date() - timedelta(days=420)).strftime("%Y%m%d"), now.date().strftime("%Y%m%d")


def akshare_history(code, kind, now=None):
    import akshare as ak
    start, end = date_range(now)
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


def sina_stock_history(code, now=None):
    """Independent Sina A-share daily fallback exposed by AKShare stock_zh_a_daily."""
    import akshare as ak
    start, end = date_range(now)
    frame = ak.stock_zh_a_daily(symbol=sina_symbol_for(code), start_date=start, end_date=end, adjust="")
    rows = frame_rows(frame)
    if len(rows) < 20:
        raise RuntimeError(f"Sina returned too few stock rows for {code}: {len(rows)}")
    return rows


def sina_fund_history(code):
    import akshare as ak
    frame = ak.fund_etf_hist_sina(symbol=sina_symbol_for(code))
    rows = frame_rows(frame)
    if len(rows) < 20:
        raise RuntimeError(f"Sina returned too few fund rows for {code}: {len(rows)}")
    return rows


def eastmoney_fund_history(code, now=None):
    now = now or datetime.now(BEIJING)
    start, end = date_range(now)
    endpoint = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    last_error = None
    for market_id in (0, 1):
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6", "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "ut": "7eea3edcaed734bea9cbfc24409ed989", "klt": "101", "fqt": "0",
            "secid": f"{market_id}.{code}", "beg": start, "end": end,
        }
        try:
            req = urllib.request.Request(endpoint + "?" + urllib.parse.urlencode(params), headers={"User-Agent": "Mozilla/5.0 investment-news/1.0"})
            with urllib.request.urlopen(req, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            klines = (payload.get("data") or {}).get("klines") or []
            rows = []
            for item in klines:
                values = item.split(",")
                if len(values) < 7 or finite(values[2]) is None:
                    continue
                rows.append({
                    "date": values[0], "open": finite(values[1]), "close": finite(values[2]),
                    "high": finite(values[3]), "low": finite(values[4]), "volume": finite(values[5]), "amount": finite(values[6]),
                })
            if len(rows) >= 20:
                return rows[-MAX_ROWS:]
            last_error = RuntimeError(f"market {market_id} returned {len(rows)} rows")
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"direct Eastmoney fund history failed for {code}: {last_error}")


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


def series(code, name, symbol, kind, rows, source, fallback_reason=None):
    last_date = rows[-1]["date"] if rows else None
    payload = {
        "code": str(code), "name": name, "symbol": symbol, "kind": kind,
        "status": fresh(last_date), "source": source,
        "last_date": last_date, "observations": len(rows), "rows": rows,
    }
    if fallback_reason:
        payload["fallback_reason"] = str(fallback_reason)[:240]
    return payload


def align_to_benchmark_date(item, benchmark_last_date):
    """Mark a series stale when it trails the benchmark's known trading date."""
    if not benchmark_last_date or not item.get("last_date"):
        return item
    if str(item["last_date"]) < str(benchmark_last_date):
        item = dict(item)
        item["status"] = "stale"
        item["staleness_reason"] = f"last_date {item['last_date']} trails benchmark {benchmark_last_date}"
    return item


def preserve(previous, code, name, symbol, kind, error, benchmark=False):
    old = previous.get("benchmark") if benchmark else previous.get("assets", {}).get(str(code))
    if old and old.get("rows"):
        kept = dict(old)
        kept["status"] = "stale"
        kept["error"] = str(error)[:240]
        return kept
    empty = series(code, name, symbol, kind, [], "unavailable")
    empty["error"] = str(error)[:240]
    return empty


def refresh(code, name, symbol, kind, previous, warnings, benchmark=False):
    primary_error = sina_error = direct_error = None
    try:
        return series(code, name, symbol, kind, akshare_history(code, kind), "东方财富 via AKShare")
    except Exception as exc:
        primary_error = exc
        warnings.append(f"{code} AKShare: {primary_error}")

    if kind == "stock":
        try:
            rows = sina_stock_history(code)
            return series(code, name, symbol, kind, rows, "新浪财经 via AKShare", primary_error)
        except Exception as exc:
            sina_error = exc
            warnings.append(f"{code} Sina stock: {sina_error}")

    if kind in {"etf", "lof"}:
        try:
            rows = sina_fund_history(code)
            return series(code, name, symbol, kind, rows, "新浪财经 via AKShare", primary_error)
        except Exception as exc:
            sina_error = exc
            warnings.append(f"{code} Sina fund: {sina_error}")
        try:
            rows = eastmoney_fund_history(code)
            return series(code, name, symbol, kind, rows, "东方财富 direct fallback", f"AKShare={primary_error}; Sina={sina_error}")
        except Exception as exc:
            direct_error = exc
            warnings.append(f"{code} Eastmoney direct: {direct_error}")

    try:
        rows = yahoo_chart(symbol)
        return series(code, name, symbol, kind, rows, "Yahoo Finance chart", f"AKShare={primary_error}; Sina={sina_error}; direct={direct_error}")
    except Exception as fallback:
        warnings.append(f"{code} Yahoo: {fallback}")
        reason = f"AKShare={primary_error}; Sina={sina_error}; direct={direct_error}; Yahoo={fallback}"
        return preserve(previous, code, name, symbol, kind, reason, benchmark)


def main():
    watchlist = load(WATCHLIST)
    previous = load(OUTPUT)
    warnings = []
    benchmark = refresh(BENCHMARK["code"], BENCHMARK["name"], BENCHMARK["symbol"], BENCHMARK["kind"], previous, warnings, benchmark=True)
    benchmark_last = benchmark.get("last_date") if benchmark.get("status") == "fresh" else None

    assets = {}
    for asset in watchlist.get("assets", []):
        code = str(asset["code"])
        item = refresh(code, asset["name"], symbol_for(code), kind_for(code), previous, warnings)
        assets[code] = align_to_benchmark_date(item, benchmark_last)
        if item.get("status") == "fresh" and assets[code].get("status") == "stale":
            warnings.append(f"{code} freshness alignment: {assets[code].get('staleness_reason')}")

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
        "methodology": "Eastmoney via AKShare primary; Sina via AKShare independent A-share/fund fallback; direct Eastmoney fund then Yahoo further fallbacks. Asset freshness is aligned to the fresh benchmark trading date; prior valid series is retained as stale on total failure; up to 140 observations retained.",
    }
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("history", payload["summary"], "benchmark", benchmark.get("status"), benchmark.get("last_date"), "warnings", len(warnings))


if __name__ == "__main__":
    main()
