#!/usr/bin/env python3
"""Combine fresh event signals with deterministic market features.

Outputs research states only (active/watch/neutral/market_watch). It never emits
portfolio sizing or brokerage instructions.
"""

import json
import math
import os
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEIJING = timezone(timedelta(hours=8))


def load_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def load_js(path):
    try:
        text = open(path, encoding="utf-8").read()
        return json.loads(text[text.index("{"):text.rindex("}") + 1])
    except (OSError, ValueError):
        return {}


def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def market_score(feature):
    score = 50.0
    rules = (
        (feature.get("ret_20d"), 10),
        (feature.get("ma20_distance"), 10),
        (feature.get("relative_strength_20d"), 10),
        (feature.get("ret_5d"), 5),
    )
    for value, weight in rules:
        if value is not None:
            score += weight if value > 0 else -weight if value < 0 else 0
    volz = feature.get("volume_z20")
    ret1 = feature.get("ret_1d")
    if volz is not None and ret1 is not None and volz >= 1:
        score += 5 if ret1 > 0 else -5 if ret1 < 0 else 0
    if feature.get("status") != "fresh":
        score = 50 + (score - 50) * 0.5
    return clamp(score)


def event_score(signals):
    if not signals:
        return 50.0
    direction = {"positive": 1, "negative": -1, "mixed": 0, "neutral": 0}
    impact = 0.0
    for signal in signals:
        strength = max(1, min(5, int(signal.get("strength", 1))))
        impact += direction.get(signal.get("direction"), 0) * strength
    impact = max(-5.0, min(5.0, impact))
    return clamp(50 + impact * 10)


def first_unique(values, limit=2):
    output = []
    for value in values:
        value = str(value).strip()
        if value and value not in output:
            output.append(value)
        if len(output) >= limit:
            break
    return output


def expiry(now, signals):
    mapping = {"intraday": 1, "1-5d": 5, "1-4w": 28, "1-3m": 90}
    days = max([mapping.get(signal.get("horizon"), 5) for signal in signals] or [5])
    return (now + timedelta(days=days)).date().isoformat()


def build():
    now = datetime.now(BEIJING)
    watchlist = load_json(os.path.join(ROOT, "watchlist.json"))
    features = load_json(os.path.join(ROOT, "features.json"))
    data = load_js(os.path.join(ROOT, "data.js"))
    ai = load_js(os.path.join(ROOT, "ai-signals.js"))

    fresh_ai = bool(
        ai.get("status") == "ready"
        and ai.get("source_generated_at")
        and ai.get("source_generated_at") == data.get("generated_at")
    )
    all_signals = ai.get("signals", []) if fresh_ai else []
    decisions = []

    for asset in watchlist.get("assets", []):
        code = str(asset["code"])
        feature = features.get("assets", {}).get(code, {})
        relevant = [signal for signal in all_signals if code in {str(x) for x in signal.get("assets", [])}]
        e_score = event_score(relevant)
        m_score = market_score(feature)
        has_event = bool(relevant)
        composite = 0.6 * e_score + 0.4 * m_score if has_event else m_score
        bias = "bullish" if composite >= 60 else "bearish" if composite <= 40 else "neutral"
        conviction = abs(composite - 50) * 2
        if not has_event:
            conviction = min(conviction, 55)
        aligned = (e_score >= 55 and m_score >= 55) or (e_score <= 45 and m_score <= 45)
        if has_event and aligned and conviction >= 55:
            status = "active"
        elif has_event and conviction >= 25:
            status = "watch"
        elif not has_event and conviction >= 30:
            status = "market_watch"
        else:
            status = "neutral"

        signal_validations = [v for signal in relevant for v in signal.get("validation", [])]
        signal_invalidations = [v for signal in relevant for v in signal.get("invalidation", [])]
        confirmations = first_unique(signal_validations + asset.get("market_validation", []))
        invalidations = first_unique(signal_invalidations + asset.get("negative_triggers", []))

        trend = feature.get("trend_state", "unknown")
        event_text = "fresh event evidence" if has_event else "no fresh mapped event"
        why_now = f"{event_text}; market trend={trend}; 20d relative strength={feature.get('relative_strength_20d')}"

        decisions.append({
            "asset": code,
            "name": asset.get("name"),
            "as_of": feature.get("as_of"),
            "bias": bias,
            "status": status,
            "event_score": round(e_score, 1),
            "market_score": round(m_score, 1),
            "freshness_score": 100 if fresh_ai and feature.get("status") == "fresh" else 70 if feature.get("status") == "fresh" else 30,
            "conviction": round(conviction, 1),
            "evidence_mode": "event_plus_market" if has_event else "market_only",
            "event_count": len(relevant),
            "trend_state": trend,
            "why_now": why_now,
            "confirmation": confirmations,
            "invalidation": invalidations,
            "expires_at": expiry(now, relevant),
        })

    payload = {
        "version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "source": {
            "data_generated_at": data.get("generated_at"),
            "ai_generated_at": ai.get("generated_at"),
            "ai_source_generated_at": ai.get("source_generated_at"),
            "features_generated_at": features.get("generated_at"),
            "fresh_ai": fresh_ai,
        },
        "decisions": decisions,
        "methodology": {
            "event_score": "50 + signed signal strength*10, aggregate capped to +/-5 strength units",
            "market_score": "50 plus deterministic signs of 20d return, MA20 distance, 20d relative strength, 5d return and high-volume 1d confirmation",
            "composite": "60% event + 40% market when a fresh mapped event exists; otherwise market score only",
            "conviction": "distance of composite from neutral, scaled 0-100; market-only conviction capped at 55",
            "status": "research state only; no position sizing or trade instruction",
        },
    }
    with open(os.path.join(ROOT, "decisions.json"), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("decisions", len(decisions), "fresh_ai", fresh_ai)


if __name__ == "__main__":
    build()
