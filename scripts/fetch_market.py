#!/usr/bin/env python3
"""Refresh source-aware quotes for the configured A-share watchlist.

AKShare/Eastmoney is the primary batch provider. Yahoo's chart endpoint is a
per-symbol fallback. A failed refresh never turns an old quote into a current
one: the last successful value is retained and explicitly marked stale.
"""

from __future__ import annotations

import json
import math
import os
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTPUT = os.path.join(ROOT, "market.json")
WATCHLIST = os.path.join(ROOT, "watchlist.json")
BEIJING = timezone(timedelta(hours=8))


def finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def exchange_for(code):
    return "SSE" if str(code).startswith(("5", "6", "9")) else "SZSE"


def yahoo_symbol(code):
    return f"{code}.{'SS' if exchange_for(code) == 'SSE' else 'SZ'}"


def status_for(as_of, today=None):
    today = today or datetime.now(BEIJING).date()
    try:
        observed = date.fromisoformat(str(as_of)[:10])
    except (TypeError, ValueError):
        return "stale"
    # Four calendar days covers normal weekends without hiding stale data.
    return "fresh" if (today - observed).days <= 4 else "stale"


def normalize_row(row, code, name, source, as_of, confidence="medium"):
    price = finite(row.get("最新价", row.get("price")))
    previous = finite(row.get("昨收", row.get("previous_close")))
    change_pct = finite(row.get("涨跌幅", row.get("change_pct")))
    if change_pct is None and price is not None and previous not in (None, 0):
        change_pct = (price / previous - 1) * 100
    return {
        "code": str(code),
        "name": name,
        "exchange": exchange_for(code),
        "price": round(price, 3) if price is not None else None,
        "previous_close": round(previous, 3) if previous is not None else None,
        "change_pct": round(change_pct, 2) if change_pct is not None else None,
        "open": finite(row.get("今开", row.get("open"))),
        "high": finite(row.get("最高", row.get("high"))),
        "low": finite(row.get("最低", row.get("low"))),
        "turnover": finite(row.get("成交额", row.get("turnover"))),
        "as_of": as_of,
        "status": status_for(as_of),
        "confidence": confidence,
        "source": source,
    }


def dataframe_by_code(frame):
    if frame is None or getattr(frame, "empty", True):
        return {}
    output = {}
    for _, row in frame.iterrows():
        values = row.to_dict()
        code = str(values.get("代码", "")).strip().zfill(6)
        if code:
            output[code] = values
    return output


def fetch_akshare(assets, now=None):
    import akshare as ak

    now = now or datetime.now(BEIJING)
    rows = {}
    errors = []
    providers = (
        ("A股", ak.stock_zh_a_spot_em),
        ("ETF", ak.fund_etf_spot_em),
        ("LOF", ak.fund_lof_spot_em),
    )
    for label, fetcher in providers:
        try:
            rows.update(dataframe_by_code(fetcher()))
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    if not rows:
        raise RuntimeError("; ".join(errors) or "AKShare returned no quote rows")
    as_of = now.isoformat(timespec="seconds")
    quotes = {}
    for asset in assets:
        code = str(asset["code"])
        if code in rows:
            quotes[code] = normalize_row(
                rows[code], code, asset["name"], "东方财富 via AKShare", as_of
            )
    return quotes, errors


def fetch_yahoo(asset, now=None):
    now = now or datetime.now(BEIJING)
    symbol = yahoo_symbol(asset["code"])
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + urllib.parse.quote(symbol)
        + "?range=5d&interval=1d"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "investment-news/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = payload["chart"]["result"][0]
    meta = result.get("meta", {})
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators", {}).get("quote", [{}])[0]
    closes = indicators.get("close") or []
    valid = [(ts, finite(value)) for ts, value in zip(timestamps, closes) if finite(value) is not None]
    if not valid:
        raise ValueError(f"Yahoo returned no close for {symbol}")
    observed_ts, price = valid[-1]
    previous = valid[-2][1] if len(valid) >= 2 else (
        finite(meta.get("regularMarketPreviousClose")) or finite(meta.get("chartPreviousClose"))
    )
    as_of = datetime.fromtimestamp(observed_ts, BEIJING).isoformat(timespec="seconds")
    row = {
        "price": finite(meta.get("regularMarketPrice")) or price,
        "previous_close": previous,
        "open": (indicators.get("open") or [None])[-1],
        "high": (indicators.get("high") or [None])[-1],
        "low": (indicators.get("low") or [None])[-1],
        "turnover": None,
    }
    return normalize_row(row, asset["code"], asset["name"], "Yahoo Finance", as_of, "low")


def unavailable_quote(asset, error):
    return {
        "code": str(asset["code"]),
        "name": asset["name"],
        "exchange": exchange_for(asset["code"]),
        "price": None,
        "previous_close": None,
        "change_pct": None,
        "as_of": None,
        "status": "unavailable",
        "confidence": "low",
        "source": "行情源待恢复",
        "error": str(error)[:240],
    }


def preserve_quote(previous, asset, error):
    old = next(
        (row for row in previous.get("quotes", []) if str(row.get("code")) == str(asset["code"])),
        None,
    )
    if not old or old.get("price") is None:
        return unavailable_quote(asset, error)
    kept = dict(old)
    kept["status"] = "stale"
    kept["error"] = str(error)[:240]
    return kept


def build_payload(assets, previous=None, now=None, batch_fetcher=fetch_akshare, fallback_fetcher=fetch_yahoo):
    previous = previous or {}
    now = now or datetime.now(BEIJING)
    warnings = []
    try:
        batch, batch_errors = batch_fetcher(assets, now=now)
        warnings.extend(batch_errors)
    except Exception as exc:
        batch = {}
        warnings.append(f"AKShare refresh failed: {exc}")
    quotes = []
    for asset in assets:
        code = str(asset["code"])
        quote = batch.get(code)
        if quote is None:
            try:
                quote = fallback_fetcher(asset, now=now)
            except Exception as exc:
                warnings.append(f"{code} refresh failed: {exc}")
                quote = preserve_quote(previous, asset, exc)
        quotes.append(quote)
    fresh = sum(row.get("status") == "fresh" for row in quotes)
    stale = sum(row.get("status") == "stale" for row in quotes)
    return {
        "version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "summary": {"total": len(quotes), "fresh": fresh, "stale": stale, "unavailable": len(quotes) - fresh - stale},
        "quotes": quotes,
        "warnings": warnings,
        "methodology": "AKShare/东方财富批量行情为主，Yahoo Finance为逐标的备用；失败时保留最近成功值并标记过期。",
    }


def load_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def write_payload(payload, path=OUTPUT):
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, path)


def main():
    watchlist = load_json(WATCHLIST)
    assets = watchlist.get("assets", [])
    payload = build_payload(assets, previous=load_json(OUTPUT))
    write_payload(payload)
    print("quotes", payload["summary"])
    for warning in payload["warnings"]:
        print("warning:", warning)


if __name__ == "__main__":
    main()
