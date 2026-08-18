#!/usr/bin/env python3
"""Fetch historical rolling P/E for selected broad CSI indices.

The engine uses the official CSI historical index endpoint exposed through
AKShare. Percentiles are calculated only from the same rolling-P/E series;
price proxies are never substituted for valuation. Failed refreshes preserve
the last successful observation as stale instead of inventing a new value.
"""

from __future__ import annotations

import json
import math
import os
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTPUT = os.path.join(ROOT, "valuation.json")
BEIJING = timezone(timedelta(hours=8))

INDEXES = [
    {"code": "000300", "name": "沪深300"},
    {"code": "000905", "name": "中证500"},
    {"code": "000852", "name": "中证1000"},
    {"code": "000906", "name": "中证800"},
]


def finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def rounded(value, digits=2):
    return round(value, digits) if value is not None and math.isfinite(value) else None


def load_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def atomic_write(payload, path=OUTPUT):
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, path)


def percentile_rank(values, current):
    clean = [float(v) for v in values if finite(v) is not None and float(v) > 0]
    if current is None or len(clean) < 20:
        return None
    return sum(v <= current for v in clean) / len(clean) * 100


def valuation_band(percentile):
    if percentile is None:
        return "insufficient"
    if percentile <= 20:
        return "very_low"
    if percentile <= 40:
        return "low"
    if percentile <= 60:
        return "neutral"
    if percentile <= 80:
        return "high"
    return "very_high"


def _iso(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)[:10]


def rows_from_frame(frame):
    rows = []
    if frame is None or getattr(frame, "empty", True):
        return rows
    for _, row in frame.iterrows():
        pe = finite(row.get("滚动市盈率"))
        observed = _iso(row.get("日期"))
        if not observed or pe is None or pe <= 0 or pe > 500:
            continue
        rows.append({"date": observed, "pe_ttm": pe})
    rows.sort(key=lambda x: x["date"])
    dedup = {}
    for row in rows:
        dedup[row["date"]] = row
    return list(dedup.values())


def nearest_value(rows, target_date):
    eligible = [row for row in rows if row["date"] <= target_date.isoformat()]
    return eligible[-1]["pe_ttm"] if eligible else None


def window_values(rows, end_date, years):
    start = end_date - timedelta(days=365 * years + 3)
    return [row["pe_ttm"] for row in rows if start.isoformat() <= row["date"] <= end_date.isoformat()]


def monthly_history(rows, years=10):
    if not rows:
        return []
    end = date.fromisoformat(rows[-1]["date"])
    start = end - timedelta(days=365 * years + 3)
    month_last = {}
    for row in rows:
        if row["date"] < start.isoformat():
            continue
        key = row["date"][:7]
        month_last[key] = {"date": row["date"], "pe_ttm": rounded(row["pe_ttm"], 2)}
    return list(month_last.values())


def summarize_rows(code, name, rows, today=None):
    today = today or datetime.now(BEIJING).date()
    if not rows:
        raise ValueError(f"no valid rolling PE observations for {code}")
    current = rows[-1]["pe_ttm"]
    as_of = date.fromisoformat(rows[-1]["date"])
    values_10y = window_values(rows, as_of, 10)
    values_5y = window_values(rows, as_of, 5)
    values_3y = window_values(rows, as_of, 3)
    p10 = percentile_rank(values_10y, current)
    status = "fresh" if (today - as_of).days <= 7 else "stale"
    return {
        "code": code,
        "name": name,
        "as_of": as_of.isoformat(),
        "status": status,
        "source": "中证指数 via AKShare stock_zh_index_hist_csindex",
        "confidence": "high" if status == "fresh" else "medium",
        "pe_ttm": rounded(current, 2),
        "pe_1m_ago": rounded(nearest_value(rows, as_of - timedelta(days=30)), 2),
        "pe_3m_ago": rounded(nearest_value(rows, as_of - timedelta(days=90)), 2),
        "percentile_3y": rounded(percentile_rank(values_3y, current), 1),
        "percentile_5y": rounded(percentile_rank(values_5y, current), 1),
        "percentile_10y": rounded(p10, 1),
        "band": valuation_band(p10),
        "observations_10y": len(values_10y),
        "history_monthly_10y": monthly_history(rows, 10),
        "metric": "滚动市盈率",
        "drives_risk_score": code == "000300",
    }


def preserve(previous, spec, error):
    old = (previous.get("indices") or {}).get(spec["code"])
    if old and old.get("pe_ttm") is not None:
        kept = dict(old)
        kept["status"] = "stale"
        kept["confidence"] = "low"
        kept["error"] = str(error)[:240]
        return kept
    return {
        "code": spec["code"],
        "name": spec["name"],
        "as_of": None,
        "status": "unavailable",
        "confidence": "low",
        "pe_ttm": None,
        "percentile_10y": None,
        "band": "insufficient",
        "drives_risk_score": spec["code"] == "000300",
        "error": str(error)[:240],
    }


def fetch_one(spec, now=None):
    import akshare as ak

    now = now or datetime.now(BEIJING)
    end = now.date()
    start = end - timedelta(days=365 * 10 + 45)
    frame = ak.stock_zh_index_hist_csindex(
        symbol=spec["code"],
        start_date=start.strftime("%Y%m%d"),
        end_date=end.strftime("%Y%m%d"),
    )
    return summarize_rows(spec["code"], spec["name"], rows_from_frame(frame), today=end)


def build_payload(previous=None, now=None, fetcher=fetch_one):
    previous = previous or {}
    now = now or datetime.now(BEIJING)
    indices = {}
    warnings = []
    for spec in INDEXES:
        try:
            indices[spec["code"]] = fetcher(spec, now=now)
        except Exception as exc:
            warnings.append(f"{spec['code']} {spec['name']}: {exc}")
            indices[spec["code"]] = preserve(previous, spec, exc)
    fresh = sum(item.get("status") == "fresh" for item in indices.values())
    return {
        "version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "summary": {"total": len(indices), "fresh": fresh, "usable": sum(item.get("pe_ttm") is not None for item in indices.values())},
        "indices": indices,
        "warnings": warnings,
        "methodology": {
            "metric": "中证指数官方历史行情中的滚动市盈率",
            "percentile": "仅在同一滚动PE序列内计算3/5/10年历史分位；不以价格分位替代估值分位。",
            "band": "10年分位≤20%极低、≤40%低、≤60%中性、≤80%高、>80%极高。",
            "risk_input": "当前仅沪深300的10年PE分位进入总风险温度，其余指数仅观察。",
        },
    }


def main():
    payload = build_payload(previous=load_json(OUTPUT))
    atomic_write(payload)
    print("valuation", payload["summary"])
    for warning in payload["warnings"]:
        print("warning:", warning)


if __name__ == "__main__":
    main()
