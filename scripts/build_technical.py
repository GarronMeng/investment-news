#!/usr/bin/env python3
"""Build explainable technical-condition snapshots from market_history.json.

The output is descriptive only. It exposes MA60 position/direction, RSI(14),
MACD state/cross age, volume state and 20-day breakout state, then records
state transitions versus the previous technical.json. It never emits buy/sell
instructions or position sizing.
"""

from __future__ import annotations

import json
import math
import os
import statistics
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INPUT = os.path.join(ROOT, "market_history.json")
OUTPUT = os.path.join(ROOT, "technical.json")
BEIJING = timezone(timedelta(hours=8))


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


def rounded(value, digits=4):
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return round(value, digits) if math.isfinite(value) else None


def sma(values, periods, end=None):
    end = len(values) if end is None else end
    if end < periods:
        return None
    window = values[end - periods:end]
    return statistics.fmean(window)


def ema_series(values, periods):
    if not values:
        return []
    alpha = 2.0 / (periods + 1)
    output = [float(values[0])]
    for value in values[1:]:
        output.append(alpha * float(value) + (1 - alpha) * output[-1])
    return output


def rsi14(values, periods=14):
    if len(values) <= periods:
        return None
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [max(change, 0.0) for change in changes]
    losses = [max(-change, 0.0) for change in changes]
    avg_gain = statistics.fmean(gains[:periods])
    avg_loss = statistics.fmean(losses[:periods])
    for i in range(periods, len(changes)):
        avg_gain = (avg_gain * (periods - 1) + gains[i]) / periods
        avg_loss = (avg_loss * (periods - 1) + losses[i]) / periods
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def rsi_zone(value):
    if value is None:
        return "insufficient"
    if value >= 70:
        return "overbought"
    if value <= 30:
        return "oversold"
    if value >= 55:
        return "strong"
    if value <= 45:
        return "weak"
    return "neutral"


def macd(values):
    if len(values) < 35:
        return {"dif": None, "dea": None, "hist": None, "state": "insufficient", "cross_age": None}
    ema12 = ema_series(values, 12)
    ema26 = ema_series(values, 26)
    dif = [a - b for a, b in zip(ema12, ema26)]
    dea = ema_series(dif, 9)
    hist = [(d - e) * 2 for d, e in zip(dif, dea)]
    state = "bullish" if dif[-1] > dea[-1] else "bearish" if dif[-1] < dea[-1] else "flat"
    cross_age = None
    for age in range(0, min(30, len(dif) - 1)):
        i = len(dif) - 1 - age
        prev = i - 1
        if prev < 0:
            break
        if state == "bullish" and dif[prev] <= dea[prev] and dif[i] > dea[i]:
            cross_age = age
            break
        if state == "bearish" and dif[prev] >= dea[prev] and dif[i] < dea[i]:
            cross_age = age
            break
    return {
        "dif": rounded(dif[-1], 5),
        "dea": rounded(dea[-1], 5),
        "hist": rounded(hist[-1], 5),
        "state": state,
        "cross_age": cross_age,
    }


def ma60_state(closes):
    current = sma(closes, 60)
    previous = sma(closes, 60, end=len(closes) - 1)
    if current is None:
        return {"value": None, "position": "insufficient", "direction": "insufficient", "slope_pct": None}
    position = "above" if closes[-1] > current else "below" if closes[-1] < current else "at"
    slope = (current / previous - 1) if previous not in (None, 0) else None
    if slope is None:
        direction = "insufficient"
    elif slope > 0.0005:
        direction = "rising"
    elif slope < -0.0005:
        direction = "falling"
    else:
        direction = "flat"
    return {
        "value": rounded(current, 4),
        "position": position,
        "direction": direction,
        "slope_pct": rounded(slope, 6),
    }


def volume_state(volumes):
    clean = [float(v) for v in volumes if v is not None]
    if len(clean) < 20:
        return {"ratio20": None, "state": "insufficient"}
    avg = statistics.fmean(clean[-20:])
    ratio = clean[-1] / avg if avg else None
    if ratio is None:
        state = "insufficient"
    elif ratio >= 1.35:
        state = "expansion"
    elif ratio <= 0.75:
        state = "contraction"
    else:
        state = "normal"
    return {"ratio20": rounded(ratio, 3), "state": state}


def breakout_state(rows):
    if len(rows) < 21:
        return "insufficient"
    close = rounded(rows[-1].get("close"), 6)
    if close is None:
        return "insufficient"
    previous = rows[-21:-1]
    highs = [rounded(row.get("high"), 6) for row in previous]
    lows = [rounded(row.get("low"), 6) for row in previous]
    highs = [v for v in highs if v is not None]
    lows = [v for v in lows if v is not None]
    if len(highs) < 15 or len(lows) < 15:
        return "insufficient"
    if close >= max(highs):
        return "new_high_20d"
    if close <= min(lows):
        return "new_low_20d"
    return "inside_range"


def condition_summary(technical):
    ma = technical["ma60"]
    checks = [
        ma.get("position") == "above",
        ma.get("direction") == "rising",
        technical["macd"].get("state") == "bullish",
        technical.get("rsi_zone") in {"neutral", "strong"},
        technical["volume"].get("state") != "contraction",
    ]
    available = [item for item in checks if isinstance(item, bool)]
    if len(available) < 4:
        return "data_insufficient"
    passed = sum(available)
    if passed == len(available):
        return "all_conditions"
    if passed >= 3:
        return "partial_conditions"
    return "conditions_not_met"


def technical_for(series):
    rows = [row for row in (series.get("rows") or []) if row.get("close") is not None]
    closes = [float(row["close"]) for row in rows]
    volumes = [row.get("volume") for row in rows]
    rsi = rsi14(closes)
    output = {
        "code": str(series.get("code") or ""),
        "name": series.get("name"),
        "as_of": series.get("last_date"),
        "source_status": series.get("status", "stale"),
        "observations": len(rows),
        "close": rounded(closes[-1], 4) if closes else None,
        "ma60": ma60_state(closes),
        "rsi14": rounded(rsi, 2),
        "rsi_zone": rsi_zone(rsi),
        "macd": macd(closes),
        "volume": volume_state(volumes),
        "breakout_20d": breakout_state(rows),
        "data_quality": "usable" if series.get("status") == "fresh" and len(rows) >= 60 else "limited",
    }
    output["condition_state"] = condition_summary(output)
    return output


def diff_states(old, new):
    fields = {
        "ma60_position": ((old.get("ma60") or {}).get("position"), (new.get("ma60") or {}).get("position")),
        "ma60_direction": ((old.get("ma60") or {}).get("direction"), (new.get("ma60") or {}).get("direction")),
        "rsi_zone": (old.get("rsi_zone"), new.get("rsi_zone")),
        "macd": ((old.get("macd") or {}).get("state"), (new.get("macd") or {}).get("state")),
        "volume": ((old.get("volume") or {}).get("state"), (new.get("volume") or {}).get("state")),
        "breakout_20d": (old.get("breakout_20d"), new.get("breakout_20d")),
        "condition_state": (old.get("condition_state"), new.get("condition_state")),
    }
    changes = []
    for field, (before, after) in fields.items():
        if before and after and before != after and "insufficient" not in {before, after}:
            changes.append({"field": field, "from": before, "to": after})
    return changes


def build(history, previous=None, now=None):
    previous = previous or {}
    now = now or datetime.now(BEIJING)
    assets = {}
    changes = []
    previous_assets = previous.get("assets", {})
    for code, series in history.get("assets", {}).items():
        item = technical_for(series)
        assets[str(code)] = item
        for change in diff_states(previous_assets.get(str(code), {}), item):
            changes.append({"code": str(code), "name": item.get("name"), **change})

    benchmark_series = history.get("benchmark", {})
    benchmark = technical_for(benchmark_series) if benchmark_series.get("rows") else {}
    return {
        "version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "source_generated_at": history.get("generated_at"),
        "benchmark": benchmark,
        "assets": assets,
        "state_changes": changes[:80],
        "methodology": {
            "rsi14": "Wilder RSI(14)",
            "macd": "EMA12/EMA26 DIF, EMA9 signal, histogram=(DIF-DEA)*2",
            "ma60": "MA60 position plus one-observation slope; ±0.05% slope band treated as flat",
            "volume": "latest volume / 20-observation average; >=1.35 expansion, <=0.75 contraction",
            "condition_state": "descriptive conjunction of MA60 position/direction, MACD, RSI zone and volume; not a trade instruction",
        },
    }


def main():
    history = load_json(INPUT)
    if not history.get("assets"):
        raise SystemExit("market_history.json is missing or empty")
    payload = build(history, previous=load_json(OUTPUT))
    atomic_write(payload)
    print("technical", len(payload["assets"]), "assets", len(payload["state_changes"]), "changes")


if __name__ == "__main__":
    main()
