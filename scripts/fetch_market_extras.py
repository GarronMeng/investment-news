#!/usr/bin/env python3
"""Fetch public market extras for the Daily Flash layer.

Coverage:
- Southbound Stock Connect net buy amount via Eastmoney/AKShare.
- CFFEX main financial futures via Sina/AKShare, with basis against the latest
  public index snapshot when an exact index mapping is available.

Failures preserve the last successful observation as stale; missing values are
never represented as zero.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "market_extras.json")
MARKET_STATE = os.path.join(ROOT, "market_state.json")
BEIJING = timezone(timedelta(hours=8))

INDEX_ALIASES = {
    "沪深300": "沪深300",
    "上证50": "上证50",
    "中证500": "中证500",
    "中证1000": "中证1000",
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


def norm_date(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:10]


def index_spots(market_state):
    rows = market_state.get("indices") or []
    if isinstance(rows, dict):
        rows = list(rows.values())
    out = {}
    for row in rows:
        name = str(row.get("name") or row.get("label") or "")
        value = finite(row.get("price", row.get("close", row.get("value"))))
        if name and value is not None:
            out[name] = value
    return out


def fetch_southbound():
    import akshare as ak

    frame = ak.stock_hsgt_fund_flow_summary_em()
    if frame is None or getattr(frame, "empty", True):
        raise RuntimeError("empty southbound summary")
    rows = [row.to_dict() for _, row in frame.iterrows()]
    south = []
    for row in rows:
        combined = "|".join(str(row.get(key, "")) for key in ("类型", "板块", "资金方向"))
        if "南向" in combined or "港股通" in combined:
            south.append(row)
    if not south:
        raise RuntimeError("southbound rows not found")
    net_values = [finite(row.get("成交净买额")) for row in south]
    net_values = [value for value in net_values if value is not None]
    inflow_values = [finite(row.get("资金净流入")) for row in south]
    inflow_values = [value for value in inflow_values if value is not None]
    if not net_values and not inflow_values:
        raise RuntimeError("southbound net values unavailable")
    dates = [norm_date(row.get("交易日")) for row in south if norm_date(row.get("交易日"))]
    statuses = [row.get("交易状态") for row in south]
    return {
        "status": "fresh",
        "as_of": max(dates) if dates else None,
        "net_buy_cny_100m": round(sum(net_values), 2) if net_values else None,
        "net_inflow_cny_100m": round(sum(inflow_values), 2) if inflow_values else None,
        "closed": bool(statuses) and all(str(value) == "3" for value in statuses if value is not None),
        "legs": [
            {
                "name": row.get("板块") or row.get("类型"),
                "net_buy_cny_100m": finite(row.get("成交净买额")),
                "net_inflow_cny_100m": finite(row.get("资金净流入")),
            }
            for row in south
        ],
        "source": "东方财富 via AKShare",
        "metric": "Stock Connect成交净买额，单位亿元",
    }


def fetch_southbound_fallback():
    import akshare as ak

    frame = ak.stock_hsgt_hist_em(symbol="南向资金")
    if frame is None or getattr(frame, "empty", True):
        raise RuntimeError("empty southbound history")
    row = frame.iloc[-1].to_dict()
    return {
        "status": "fresh",
        "as_of": norm_date(row.get("日期")),
        "net_buy_cny_100m": finite(row.get("当日成交净买额")),
        "net_inflow_cny_100m": finite(row.get("当日资金流入")),
        "closed": True,
        "legs": [],
        "source": "东方财富历史数据 via AKShare",
        "metric": "南向资金当日成交净买额，单位亿元",
    }


def future_underlying(symbol_text):
    text = str(symbol_text or "")
    for key in INDEX_ALIASES:
        if key in text:
            return INDEX_ALIASES[key]
    return None


def fetch_futures(market_state):
    import akshare as ak

    subscriptions = ak.match_main_contract(symbol="cffex")
    if not subscriptions:
        raise RuntimeError("CFFEX main contract list unavailable")
    frame = ak.futures_zh_spot(symbol=subscriptions, market="FF", adjust="0")
    if frame is None or getattr(frame, "empty", True):
        raise RuntimeError("CFFEX quote table empty")
    spots = index_spots(market_state)
    output = []
    for _, series in frame.iterrows():
        row = series.to_dict()
        label = str(row.get("symbol") or "")
        underlying = future_underlying(label)
        if not underlying:
            continue
        current = finite(row.get("current_price"))
        last_close = finite(row.get("last_close"))
        spot = spots.get(underlying)
        basis = current - spot if current is not None and spot is not None else None
        basis_pct = basis / spot * 100 if basis is not None and spot not in (None, 0) else None
        change_pct = (current / last_close - 1) * 100 if current is not None and last_close not in (None, 0) else None
        output.append({
            "symbol": label,
            "underlying": underlying,
            "current_price": round(current, 3) if current is not None else None,
            "change_pct": round(change_pct, 2) if change_pct is not None else None,
            "spot": round(spot, 3) if spot is not None else None,
            "basis": round(basis, 3) if basis is not None else None,
            "basis_pct": round(basis_pct, 3) if basis_pct is not None else None,
            "hold": finite(row.get("hold")),
            "volume": finite(row.get("volume")),
            "time": row.get("time"),
            "status": "fresh",
            "source": "新浪财经 via AKShare",
        })
    if not output:
        raise RuntimeError("no mapped CFFEX index futures in quote table")
    return output


def preserve(previous, key, error):
    old = previous.get(key)
    if old:
        if isinstance(old, dict):
            kept = dict(old)
            kept["status"] = "stale"
            kept["error"] = str(error)[:240]
            return kept
        if isinstance(old, list):
            kept = []
            for row in old:
                item = dict(row)
                item["status"] = "stale"
                item["error"] = str(error)[:240]
                kept.append(item)
            return kept
    return None


def build(previous=None, market_state=None, now=None):
    previous = previous or {}
    market_state = market_state or {}
    now = now or datetime.now(BEIJING)
    warnings = []
    try:
        southbound = fetch_southbound()
    except Exception as exc:
        warnings.append(f"southbound summary: {exc}")
        try:
            southbound = fetch_southbound_fallback()
            southbound["fallback"] = True
        except Exception as fallback_exc:
            warnings.append(f"southbound fallback: {fallback_exc}")
            southbound = preserve(previous, "southbound", fallback_exc) or {
                "status": "unavailable", "as_of": None, "net_buy_cny_100m": None,
                "net_inflow_cny_100m": None, "legs": [], "source": "数据源待恢复",
            }
    try:
        futures = fetch_futures(market_state)
    except Exception as exc:
        warnings.append(f"cffex futures: {exc}")
        futures = preserve(previous, "index_futures", exc) or []
    return {
        "version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "southbound": southbound,
        "index_futures": futures,
        "warnings": warnings,
        "methodology": {
            "southbound": "东方财富沪深港通资金流向，经AKShare标准化；优先汇总南向/港股通成交净买额，失败时回退南向资金历史数据。单位亿元。",
            "index_futures": "新浪财经CFFEX主力金融期货经AKShare获取；仅对能与market_state中精确同名现货指数匹配的合约计算基差。",
            "boundary": "市场补充指标仅描述资金与基差状态，不构成交易指令。",
        },
    }


def main():
    payload = build(previous=load_json(OUTPUT), market_state=load_json(MARKET_STATE))
    tmp = OUTPUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(tmp, OUTPUT)
    print("market extras", "southbound", payload["southbound"].get("net_buy_cny_100m"), "futures", len(payload["index_futures"]))
    for warning in payload["warnings"]:
        print("warning:", warning)


if __name__ == "__main__":
    main()
