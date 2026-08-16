#!/usr/bin/env python3
"""Build deterministic market features from market_history.json."""

import json
import math
import os
import statistics
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INPUT = os.path.join(ROOT, "market_history.json")
OUTPUT = os.path.join(ROOT, "features.json")
BEIJING = timezone(timedelta(hours=8))


def load_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def pct_return(values, periods):
    if len(values) <= periods or values[-periods - 1] in (None, 0):
        return None
    return values[-1] / values[-periods - 1] - 1


def mean_distance(values, periods):
    if len(values) < periods:
        return None
    avg = statistics.fmean(values[-periods:])
    return values[-1] / avg - 1 if avg else None


def zscore(values, periods=20):
    clean = [float(v) for v in values[-periods:] if v is not None]
    if len(clean) < periods:
        return None
    sd = statistics.pstdev(clean)
    return (clean[-1] - statistics.fmean(clean)) / sd if sd else 0.0


def realized_vol(closes, periods=20):
    if len(closes) < periods + 1:
        return None
    logs = [math.log(closes[i] / closes[i - 1]) for i in range(len(closes) - periods, len(closes)) if closes[i - 1] > 0 and closes[i] > 0]
    if len(logs) < periods:
        return None
    return statistics.pstdev(logs) * math.sqrt(252)


def drawdown(closes, periods=20):
    if len(closes) < periods:
        return None
    window = closes[-periods:]
    peak = max(window)
    return closes[-1] / peak - 1 if peak else None


def rounded(value, digits=6):
    return round(value, digits) if value is not None and math.isfinite(value) else None


def feature_for(series, benchmark_returns):
    rows = series.get("rows") or []
    closes = [float(row["close"]) for row in rows if row.get("close") is not None]
    volumes = [row.get("volume") for row in rows]
    ret1 = pct_return(closes, 1)
    ret5 = pct_return(closes, 5)
    ret20 = pct_return(closes, 20)
    rs5 = ret5 - benchmark_returns.get("ret_5d") if ret5 is not None and benchmark_returns.get("ret_5d") is not None else None
    rs20 = ret20 - benchmark_returns.get("ret_20d") if ret20 is not None and benchmark_returns.get("ret_20d") is not None else None
    ma20 = mean_distance(closes, 20)
    ma60 = mean_distance(closes, 60)
    volz = zscore(volumes, 20)

    positive = sum(value is not None and value > 0 for value in (ret20, ma20, rs20))
    negative = sum(value is not None and value < 0 for value in (ret20, ma20, rs20))
    trend = "bullish" if positive == 3 else "bearish" if negative == 3 else "mixed"

    return {
        "code": series.get("code"),
        "name": series.get("name"),
        "as_of": series.get("last_date"),
        "status": series.get("status", "stale"),
        "observations": len(rows),
        "ret_1d": rounded(ret1),
        "ret_5d": rounded(ret5),
        "ret_20d": rounded(ret20),
        "ma20_distance": rounded(ma20),
        "ma60_distance": rounded(ma60),
        "volume_z20": rounded(volz, 4),
        "turnover_z20": None,
        "relative_strength_5d": rounded(rs5),
        "relative_strength_20d": rounded(rs20),
        "realized_vol_20d": rounded(realized_vol(closes, 20)),
        "drawdown_20d": rounded(drawdown(closes, 20)),
        "trend_state": trend,
    }


def build(history):
    benchmark = history.get("benchmark", {})
    bench_closes = [float(row["close"]) for row in benchmark.get("rows", []) if row.get("close") is not None]
    bench_returns = {
        "ret_1d": pct_return(bench_closes, 1),
        "ret_5d": pct_return(bench_closes, 5),
        "ret_20d": pct_return(bench_closes, 20),
    }
    assets = {
        code: feature_for(series, bench_returns)
        for code, series in history.get("assets", {}).items()
    }
    return {
        "version": 1,
        "generated_at": datetime.now(BEIJING).isoformat(timespec="seconds"),
        "source_generated_at": history.get("generated_at"),
        "benchmark": {
            "code": benchmark.get("code"),
            "name": benchmark.get("name"),
            "as_of": benchmark.get("last_date"),
            "status": benchmark.get("status"),
            **{key: rounded(value) for key, value in bench_returns.items()},
        },
        "assets": assets,
        "methodology": {
            "returns": "close-to-close total price return, unadjusted",
            "relative_strength": "asset return minus benchmark return",
            "volume_z20": "population z-score of the latest volume within 20 observations",
            "turnover_z20": "unavailable in the current history feed; never imputed",
            "realized_vol_20d": "20-day log-return volatility annualized by sqrt(252)",
            "trend_state": "bullish/bearish only when ret20, MA20 distance and 20d relative strength agree; otherwise mixed",
        },
    }


def main():
    history = load_json(INPUT)
    if not history.get("assets"):
        raise SystemExit("market_history.json is missing or empty")
    payload = build(history)
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("features", len(payload["assets"]), "assets")


if __name__ == "__main__":
    main()
