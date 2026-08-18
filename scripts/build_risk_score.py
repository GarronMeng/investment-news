#!/usr/bin/env python3
"""Build an explainable market risk temperature from public inputs.

Higher score means a more fragile/stressed valuation + structure + trend +
sentiment environment. Missing components are excluded and remaining weights
are renormalized; the output exposes coverage so absence of data is visible.
The score is descriptive and is not a probability or trading instruction.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTPUT = os.path.join(ROOT, "risk_score.json")
BEIJING = timezone(timedelta(hours=8))

WEIGHTS = {
    "valuation": 20,
    "market_structure": 25,
    "trend": 20,
    "leverage": 15,
    "overseas": 10,
    "concentration": 10,
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


def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def rounded(value, digits=1):
    return round(value, digits) if value is not None and math.isfinite(value) else None


def metric(metrics, metric_id):
    for item in metrics or []:
        if item.get("id") == metric_id:
            return item
    return {}


def valuation_component(valuation):
    item = (valuation.get("indices") or {}).get("000300", {})
    p = finite(item.get("percentile_10y"))
    if p is None or item.get("status") == "unavailable":
        return None, "沪深300估值分位不可用"
    return clamp(p), f"沪深300滚动PE十年分位 {p:.1f}%"


def market_structure_component(state):
    regime = (state.get("regime") or {}).get("code")
    base = {
        "risk_on": 30,
        "narrow_risk_on": 58,
        "transition": 65,
        "risk_off": 88,
    }.get(regime)
    adv = finite((state.get("breadth") or {}).get("advance_ratio"))
    breadth_risk = None if adv is None else clamp((1 - adv) * 100)
    if base is None and breadth_risk is None:
        return None, "市场结构不可用"
    if base is None:
        score = breadth_risk
    elif breadth_risk is None:
        score = base
    else:
        score = 0.6 * base + 0.4 * breadth_risk
    text = f"{regime or 'regime缺失'}"
    if adv is not None:
        text += f"；上涨占比 {adv * 100:.1f}%"
    return clamp(score), text


def trend_component(technical):
    bench = technical.get("benchmark") or {}
    if not bench or bench.get("data_quality") == "limited":
        return None, "基准技术状态不可用"
    score = 45.0
    ma = bench.get("ma60") or {}
    macd = bench.get("macd") or {}
    rsi_zone = bench.get("rsi_zone")
    score += 20 if ma.get("position") == "below" else -12 if ma.get("position") == "above" else 0
    score += 14 if ma.get("direction") == "falling" else -8 if ma.get("direction") == "rising" else 0
    score += 10 if macd.get("state") == "bearish" else -6 if macd.get("state") == "bullish" else 0
    if rsi_zone == "overbought":
        score += 10
    elif rsi_zone == "oversold":
        score += 6
    elif rsi_zone == "strong":
        score -= 4
    text = f"MA60 {ma.get('position','—')}/{ma.get('direction','—')}；MACD {macd.get('state','—')}；RSI {rsi_zone or '—'}"
    return clamp(score), text


def leverage_component(sentiment):
    item = metric(sentiment.get("metrics"), "margin_balance")
    if not item or item.get("status") == "unavailable":
        return None, "两融数据不可用"
    z = finite(item.get("zscore_20d"))
    change5 = finite(item.get("change_5d_pct"))
    if z is not None:
        score = clamp(50 + z * 18)
        return score, f"两融20日Z {z:.2f}"
    if change5 is not None:
        score = clamp(50 + change5 * 8)
        return score, f"两融5日变化 {change5:.2f}%（20日基线尚未完整）"
    return 50.0, "两融可用但基线不足，按中性计"


def overseas_component(sentiment):
    item = metric(sentiment.get("metrics"), "vix")
    if not item or item.get("status") == "unavailable":
        return None, "VIX不可用"
    p = finite(item.get("percentile_20d"))
    value = finite(item.get("value"))
    if p is not None:
        absolute = clamp(((value or 15) - 12) * 4.0) if value is not None else 0
        score = clamp(0.75 * p + 0.25 * absolute)
        return score, f"VIX {value:.2f}；20日分位 {p:.1f}%" if value is not None else f"VIX 20日分位 {p:.1f}%"
    if value is not None:
        return clamp((value - 10) * 5), f"VIX {value:.2f}"
    return None, "VIX不可用"


def concentration_component(state):
    regime = (state.get("regime") or {}).get("code")
    adv = finite((state.get("breadth") or {}).get("advance_ratio"))
    index_changes = [finite(x.get("change_pct")) for x in state.get("indices") or []]
    index_changes = [x for x in index_changes if x is not None]
    mean_index = sum(index_changes) / len(index_changes) if index_changes else None
    if regime == "narrow_risk_on":
        score = 82.0
    elif regime == "transition":
        score = 58.0
    elif regime == "risk_off":
        score = 66.0
    elif regime == "risk_on":
        score = 30.0
    elif adv is not None and mean_index is not None:
        score = 75.0 if mean_index > 0 and adv < 0.45 else 45.0
    else:
        return None, "集中度代理不可用"
    text = f"regime={regime or '—'}"
    if mean_index is not None and adv is not None:
        text += f"；指数均值 {mean_index:.2f}% / 上涨占比 {adv*100:.1f}%"
    return score, text


def risk_label(score):
    if score is None:
        return "insufficient"
    if score < 35:
        return "low"
    if score < 55:
        return "balanced"
    if score < 70:
        return "elevated"
    return "high"


def build(valuation, state, technical, sentiment, previous=None, now=None):
    previous = previous or {}
    now = now or datetime.now(BEIJING)
    builders = {
        "valuation": lambda: valuation_component(valuation),
        "market_structure": lambda: market_structure_component(state),
        "trend": lambda: trend_component(technical),
        "leverage": lambda: leverage_component(sentiment),
        "overseas": lambda: overseas_component(sentiment),
        "concentration": lambda: concentration_component(state),
    }
    components = {}
    weighted_sum = 0.0
    available_weight = 0.0
    for key, weight in WEIGHTS.items():
        score, evidence = builders[key]()
        available = score is not None
        components[key] = {
            "score": rounded(score),
            "weight": weight,
            "available": available,
            "evidence": evidence,
        }
        if available:
            weighted_sum += score * weight
            available_weight += weight
    total = weighted_sum / available_weight if available_weight else None
    label = risk_label(total)
    drivers = sorted(
        [
            {"component": key, "score": item["score"], "evidence": item["evidence"]}
            for key, item in components.items() if item["available"]
        ],
        key=lambda x: x["score"],
        reverse=True,
    )[:3]
    old_score = finite(previous.get("score"))
    old_label = previous.get("label")
    changes = []
    if old_label and old_label != label and label != "insufficient":
        changes.append({"type": "label", "from": old_label, "to": label})
    if old_score is not None and total is not None and abs(total - old_score) >= 10:
        changes.append({"type": "score", "from": rounded(old_score), "to": rounded(total)})
    return {
        "version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "score": rounded(total),
        "label": label,
        "coverage": rounded(available_weight / sum(WEIGHTS.values()) * 100, 1),
        "available_weight": int(available_weight),
        "components": components,
        "drivers": drivers,
        "state_changes": changes,
        "methodology": "估值20% + 市场结构25% + 基准趋势20% + 两融15% + 海外风险10% + 集中度10%。缺失项剔除并按可用权重重新归一；高分表示环境更脆弱/压力更高，不是下跌概率。",
        "boundary": "风险温度只做环境校准，不生成买卖、仓位或止损指令。",
    }


def main():
    valuation = load_json(os.path.join(ROOT, "valuation.json"))
    state = load_json(os.path.join(ROOT, "market_state.json"))
    technical = load_json(os.path.join(ROOT, "technical.json"))
    sentiment = load_json(os.path.join(ROOT, "sentiment.json"))
    previous = load_json(OUTPUT)
    payload = build(valuation, state, technical, sentiment, previous=previous)
    temporary = OUTPUT + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, OUTPUT)
    print("risk score", payload["score"], payload["label"], "coverage", payload["coverage"])


if __name__ == "__main__":
    main()
