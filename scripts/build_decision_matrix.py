#!/usr/bin/env python3
"""Build a transparent multi-layer research decision matrix.

The matrix combines five evidence layers for each watchlist asset:
1) fresh mapped event evidence, 2) technical structure, 3) relative strength,
4) industry breadth/flow when a mapped sector is actually observed, and
5) broad A-share market context for equity-like assets.

Outputs are research states only. Missing layers are excluded and weights are
renormalized; absence is never treated as zero. The engine never emits trade,
position-size, stop-loss, quantity or cost-basis instructions.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTPUT = os.path.join(ROOT, "decision_matrix.json")
BEIJING = timezone(timedelta(hours=8))

WEIGHTS = {
    "event": 25,
    "technical": 30,
    "relative_strength": 20,
    "industry": 15,
    "market_context": 10,
}

# Public watchlist taxonomy -> observable A-share industry labels.
# Matching is intentionally conservative: only sectors that actually appear in
# market_state top/bottom or fund-flow tables can contribute to the score.
SECTOR_ALIASES = {
    "semi": ["半导体", "元件", "集成电路", "电子化学品", "光学光电子"],
    "consumer": ["消费电子", "元件", "光学光电子"],
    "ai": ["通信设备", "通信服务", "IT服务", "半导体", "光学光电子"],
    "tech": ["通信设备", "通信服务", "IT服务", "计算机设备", "软件开发", "半导体"],
    "auto": ["汽车零部件", "汽车整车", "电池"],
    "bio": ["生物制品", "医疗服务", "化学制药", "医疗器械"],
    "energy": ["油气开采及服务", "煤炭开采加工", "燃气", "电力"],
    "macro": [],
}

HEDGE_GROUPS = {"贵金属对冲"}


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


def finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def clamp(value, low=-100.0, high=100.0):
    return max(low, min(high, float(value)))


def rounded(value, digits=1):
    return round(float(value), digits) if value is not None and math.isfinite(float(value)) else None


def sign(value, threshold=15.0):
    value = finite(value)
    if value is None or abs(value) < threshold:
        return 0
    return 1 if value > 0 else -1


def event_layer(decision):
    count = int(decision.get("event_count") or 0)
    if count <= 0:
        return {
            "available": False,
            "score": None,
            "confidence": "none",
            "evidence": "无新鲜映射事件；该层不参与合成。",
        }
    score = finite(decision.get("event_score"))
    if score is None:
        return {"available": False, "score": None, "confidence": "none", "evidence": "事件分数缺失。"}
    signed = clamp((score - 50.0) * 2.0)
    return {
        "available": True,
        "score": rounded(signed),
        "confidence": "high" if decision.get("evidence_mode") == "event_plus_market" else "medium",
        "evidence": f"{count} 条新鲜映射事件；event_score={score:.1f}/100。",
    }


def technical_layer(item):
    if not item or item.get("data_quality") != "usable":
        return {"available": False, "score": None, "confidence": "none", "evidence": "技术数据不足。"}
    score = 0.0
    ma = item.get("ma60") or {}
    score += {"above": 22, "below": -22, "at": 0}.get(ma.get("position"), 0)
    score += {"rising": 22, "falling": -22, "flat": 0}.get(ma.get("direction"), 0)
    score += {"bullish": 24, "bearish": -24, "flat": 0}.get((item.get("macd") or {}).get("state"), 0)
    score += {
        "strong": 14, "weak": -14, "neutral": 0,
        "overbought": 6, "oversold": -6,
    }.get(item.get("rsi_zone"), 0)
    score += {"new_high_20d": 12, "new_low_20d": -12, "inside_range": 0}.get(item.get("breakout_20d"), 0)
    volume_state = (item.get("volume") or {}).get("state")
    confidence = "high" if volume_state in {"normal", "expansion"} else "medium"
    evidence = (
        f"MA60 {ma.get('position','?')}/{ma.get('direction','?')}；"
        f"MACD {(item.get('macd') or {}).get('state','?')}；"
        f"RSI {item.get('rsi14','?')} ({item.get('rsi_zone','?')})；"
        f"量能 {volume_state or '?'}；20日结构 {item.get('breakout_20d','?')}。"
    )
    return {"available": True, "score": rounded(clamp(score)), "confidence": confidence, "evidence": evidence}


def relative_strength_layer(feature):
    if not feature or feature.get("status") not in {"fresh", "stale"}:
        return {"available": False, "score": None, "confidence": "none", "evidence": "相对强弱数据不足。"}
    rs5 = finite(feature.get("relative_strength_5d"))
    rs20 = finite(feature.get("relative_strength_20d"))
    if rs5 is None and rs20 is None:
        return {"available": False, "score": None, "confidence": "none", "evidence": "相对强弱字段缺失。"}
    parts = []
    if rs20 is not None:
        parts.append((65, math.tanh(rs20 / 0.12) * 100))
    if rs5 is not None:
        parts.append((35, math.tanh(rs5 / 0.06) * 100))
    total = sum(weight for weight, _ in parts)
    score = sum(weight * value for weight, value in parts) / total
    evidence = f"5日相对强弱 {rs5 if rs5 is not None else '—'}；20日相对强弱 {rs20 if rs20 is not None else '—'}。"
    return {
        "available": True,
        "score": rounded(clamp(score)),
        "confidence": "high" if feature.get("status") == "fresh" else "medium",
        "evidence": evidence,
    }


def _market_sector_rows(market_state):
    rows = {}
    for key in ("leaders", "laggards"):
        for row in (market_state.get("sectors") or {}).get(key, []) or []:
            name = str(row.get("name") or "")
            if name:
                slot = rows.setdefault(name, {})
                slot["change_pct"] = finite(row.get("change_pct"))
                slot["source"] = row.get("source")
    for key in ("inflow", "outflow"):
        for row in (market_state.get("industry_flow") or {}).get(key, []) or []:
            name = str(row.get("name") or "")
            if name:
                slot = rows.setdefault(name, {})
                if finite(row.get("change_pct")) is not None:
                    slot["change_pct"] = finite(row.get("change_pct"))
                slot["net_inflow"] = finite(row.get("net_inflow"))
                slot["source"] = row.get("source") or slot.get("source")
    return rows


def industry_layer(asset, market_state):
    aliases = []
    for industry in asset.get("industries") or []:
        aliases.extend(SECTOR_ALIASES.get(industry, []))
    aliases = list(dict.fromkeys(aliases))
    if not aliases:
        return {
            "available": False,
            "score": None,
            "confidence": "none",
            "evidence": "该标的暂无可审计的A股行业映射；行业层不参与合成。",
            "matches": [],
        }
    observed = _market_sector_rows(market_state)
    matches = [(name, observed[name]) for name in aliases if name in observed]
    if not matches:
        return {
            "available": False,
            "score": None,
            "confidence": "none",
            "evidence": "映射行业未进入当前强弱/资金榜；缺失不按中性处理。",
            "matches": [],
        }
    scored = []
    details = []
    for name, row in matches:
        pct = finite(row.get("change_pct"))
        flow = finite(row.get("net_inflow"))
        pieces = []
        if pct is not None:
            pieces.append((0.45, clamp(pct / 3.0 * 100)))
        if flow is not None:
            # 20bn yuan is deliberately a soft saturation scale; tanh avoids
            # one extreme industry observation dominating the entire matrix.
            pieces.append((0.55, math.tanh(flow / 20_000_000_000) * 100))
        if pieces:
            denom = sum(weight for weight, _ in pieces)
            sector_score = sum(weight * value for weight, value in pieces) / denom
            scored.append(sector_score)
            flow_text = f"{flow/1e8:.1f}亿" if flow is not None else "—"
            pct_text = f"{pct:+.2f}%" if pct is not None else "—"
            details.append(f"{name} 涨跌{pct_text}/净流{flow_text}")
    if not scored:
        return {"available": False, "score": None, "confidence": "none", "evidence": "行业榜有名称但无可用数值。", "matches": []}
    score = sum(scored) / len(scored)
    return {
        "available": True,
        "score": rounded(clamp(score)),
        "confidence": "medium" if len(scored) >= 2 else "low",
        "evidence": "；".join(details[:4]),
        "matches": [name for name, _ in matches],
    }


def market_context_layer(asset, market_state, risk):
    if asset.get("group") in HEDGE_GROUPS:
        return {
            "available": False,
            "score": None,
            "confidence": "none",
            "evidence": "贵金属对冲不使用A股风险温度作为方向证据。",
        }
    regime = (market_state.get("regime") or {}).get("code")
    regime_score = {
        "risk_on": 70, "narrow_risk_on": 35, "transition": 0,
        "risk_off": -70,
    }.get(regime)
    adv = finite((market_state.get("breadth") or {}).get("advance_ratio"))
    risk_score = finite(risk.get("score"))
    parts = []
    if regime_score is not None:
        parts.append((0.40, regime_score))
    if adv is not None:
        parts.append((0.30, clamp((adv - 0.5) * 200)))
    if risk_score is not None:
        parts.append((0.30, clamp((50.0 - risk_score) * 1.6)))
    if not parts:
        return {"available": False, "score": None, "confidence": "none", "evidence": "市场环境数据不足。"}
    denom = sum(weight for weight, _ in parts)
    score = sum(weight * value for weight, value in parts) / denom
    evidence = f"regime={regime or '—'}；上涨占比={adv if adv is not None else '—'}；风险温度={risk_score if risk_score is not None else '—'}。"
    return {"available": True, "score": rounded(clamp(score)), "confidence": "medium", "evidence": evidence}


def combine_layers(layers):
    available = [(name, layer, WEIGHTS[name]) for name, layer in layers.items() if layer.get("available") and finite(layer.get("score")) is not None]
    available_weight = sum(weight for _, _, weight in available)
    if available_weight == 0:
        return None, 0.0, 0.0, 0, 0.0
    composite = sum(weight * float(layer["score"]) for _, layer, weight in available) / available_weight
    coverage = available_weight / sum(WEIGHTS.values()) * 100
    directional = [(name, layer, weight) for name, layer, weight in available if sign(layer.get("score"))]
    direction_sign = sign(composite, threshold=20)
    if direction_sign and directional:
        directional_weight = sum(weight for _, _, weight in directional)
        agree_weight = sum(weight for _, layer, weight in directional if sign(layer.get("score")) == direction_sign)
        agreement = agree_weight / directional_weight * 100 if directional_weight else 0.0
    else:
        agreement = 0.0
    confluence = min(100.0, agreement * 0.7 + abs(composite) * 0.3) if direction_sign else min(45.0, abs(composite) * 1.5)
    opposing_weight = 0.0
    if direction_sign:
        opposing_weight = sum(weight for _, layer, weight in directional if sign(layer.get("score")) == -direction_sign)
    opposing_share = opposing_weight / available_weight * 100 if available_weight else 0.0
    return rounded(composite), rounded(coverage), rounded(confluence), len(available), rounded(opposing_share)


def direction_from_score(score):
    if score is None:
        return "insufficient"
    if score >= 20:
        return "bullish"
    if score <= -20:
        return "bearish"
    return "neutral"


def evidence_state(direction, composite, confluence, coverage, layer_count, opposing_share):
    if layer_count < 3 or coverage < 50:
        return "insufficient"
    if direction == "neutral":
        if opposing_share >= 20:
            return "conflict"
        return "noise_or_no_edge"
    if opposing_share >= 30:
        return "conflict"
    if confluence >= 72 and abs(composite or 0) >= 38:
        return "multi_layer_confirmed"
    if confluence >= 55:
        return "partial_confirmation"
    return "tentative"


def thesis_state(base_bias, direction, evidence):
    if base_bias not in {"bullish", "bearish"}:
        if direction in {"bullish", "bearish"} and evidence in {"multi_layer_confirmed", "partial_confirmation"}:
            return "emerging"
        if evidence == "conflict":
            return "conflicted"
        return "no_directional_thesis"
    if direction == base_bias:
        if evidence == "multi_layer_confirmed":
            return "confirmed"
        return "supported"
    if direction == "neutral":
        return "under_test"
    if evidence in {"multi_layer_confirmed", "partial_confirmation"}:
        return "contradicted"
    return "conflicted"


def research_focus(thesis, evidence):
    if thesis == "confirmed":
        return "验证持续性、行业扩散与后续基本面证据。"
    if thesis == "supported":
        return "维持观察，等待更多层形成共振。"
    if thesis == "contradicted":
        return "优先复核原假设的失效条件与事件时效。"
    if thesis in {"conflicted", "under_test"} or evidence == "conflict":
        return "暂不提高确信度，观察冲突证据如何消解。"
    if thesis == "emerging":
        return "出现新方向，但先等待事件或行业证据确认。"
    if evidence == "noise_or_no_edge":
        return "当前更接近价格噪声/无明显边际，维持低优先级观察。"
    return "数据或证据覆盖不足，先补齐关键层。"


def top_contributors(layers):
    items = []
    for name, layer in layers.items():
        score = finite(layer.get("score"))
        if not layer.get("available") or score is None:
            continue
        impact = score * WEIGHTS[name] / 100.0
        items.append((impact, name, score, layer.get("evidence")))
    positive = sorted((x for x in items if x[0] > 0), reverse=True)[:2]
    negative = sorted((x for x in items if x[0] < 0))[:2]
    return {
        "positive": [{"layer": name, "score": rounded(score), "evidence": evidence} for _, name, score, evidence in positive],
        "negative": [{"layer": name, "score": rounded(score), "evidence": evidence} for _, name, score, evidence in negative],
    }


def attention_score(asset, thesis, evidence, confluence, priority):
    base = {"contradicted": 92, "conflicted": 78, "under_test": 68, "confirmed": 62, "emerging": 60, "supported": 52, "no_directional_thesis": 35}.get(thesis, 40)
    if evidence == "insufficient":
        base = max(base, 55)
    base += max(0, min(10, (priority or 3) * 2 - 4))
    base += min(8, (confluence or 0) / 15)
    return rounded(min(100, base))


def build(watch, decisions, technical, features, market_state, risk, previous=None, now=None):
    previous = previous or {}
    now = now or datetime.now(BEIJING)
    decision_map = {str(item.get("asset")): item for item in decisions.get("decisions", [])}
    tech_map = technical.get("assets", {})
    feature_map = features.get("assets", {})
    old_assets = previous.get("assets", {})
    assets = {}
    changes = []

    for asset in watch.get("assets", []):
        code = str(asset.get("code"))
        decision = decision_map.get(code, {})
        layers = {
            "event": event_layer(decision),
            "technical": technical_layer(tech_map.get(code, {})),
            "relative_strength": relative_strength_layer(feature_map.get(code, {})),
            "industry": industry_layer(asset, market_state),
            "market_context": market_context_layer(asset, market_state, risk),
        }
        composite, coverage, confluence, layer_count, opposing_share = combine_layers(layers)
        direction = direction_from_score(composite)
        evidence = evidence_state(direction, composite, confluence, coverage, layer_count, opposing_share)
        base_bias = decision.get("bias") if decision.get("bias") in {"bullish", "bearish"} else "neutral"
        thesis = thesis_state(base_bias, direction, evidence)
        item = {
            "code": code,
            "name": asset.get("name"),
            "group": asset.get("group"),
            "role": asset.get("role"),
            "priority": asset.get("priority"),
            "as_of": decision.get("as_of") or technical.get("source_generated_at"),
            "base_bias": base_bias,
            "matrix_direction": direction,
            "composite_score": composite,
            "coverage": coverage,
            "confluence": confluence,
            "available_layers": layer_count,
            "opposing_weight_share": opposing_share,
            "evidence_state": evidence,
            "thesis_state": thesis,
            "attention_score": attention_score(asset, thesis, evidence, confluence, asset.get("priority")),
            "research_focus": research_focus(thesis, evidence),
            "layers": layers,
            "contributors": top_contributors(layers),
            "confirmation": (decision.get("confirmation") or [])[:2],
            "invalidation": (decision.get("invalidation") or [])[:2],
        }
        assets[code] = item
        old = old_assets.get(code, {})
        for field in ("matrix_direction", "evidence_state", "thesis_state"):
            before, after = old.get(field), item.get(field)
            if before and after and before != after:
                changes.append({"code": code, "name": item["name"], "field": field, "from": before, "to": after})

    ordered = sorted(assets.values(), key=lambda x: (-float(x.get("attention_score") or 0), int(x.get("priority") or 0) * -1, x.get("name") or ""))
    summary = {
        "total": len(assets),
        "confirmed": sum(item["thesis_state"] == "confirmed" for item in assets.values()),
        "supported": sum(item["thesis_state"] == "supported" for item in assets.values()),
        "contradicted": sum(item["thesis_state"] == "contradicted" for item in assets.values()),
        "conflicted": sum(item["thesis_state"] in {"conflicted", "under_test"} for item in assets.values()),
        "emerging": sum(item["thesis_state"] == "emerging" for item in assets.values()),
        "insufficient": sum(item["evidence_state"] == "insufficient" for item in assets.values()),
        "top_attention": [item["code"] for item in ordered[:5]],
    }
    return {
        "version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "summary": summary,
        "assets": assets,
        "ranking": [item["code"] for item in ordered],
        "state_changes": changes[:30],
        "methodology": {
            "weights": WEIGHTS,
            "composite": "各可用层使用固定权重后按可用权重重新归一；缺失层不视为0。分数为证据方向强弱，不是收益概率。",
            "event": "decisions.json fresh mapped event_score 转换为 -100..100；无新鲜事件时该层缺失。",
            "technical": "MA60位置/方向、MACD、RSI、20日突破结构；量能只影响置信度。",
            "relative_strength": "5日与20日相对沪深300基准强弱，经tanh压缩极值。",
            "industry": "只使用实际出现在行业强弱或资金榜的映射行业；未上榜不按中性处理。",
            "market_context": "A股regime、上涨家数占比和风险温度；贵金属对冲标的明确排除该方向层。",
            "confluence": "衡量已有方向证据的一致程度；不是预测胜率。",
        },
        "boundary": "仅用于研究优先级、假设验证与冲突识别；不生成买卖、仓位、止损、数量或成本相关指令。",
    }


def main():
    paths = {
        "watch": os.path.join(ROOT, "watchlist.json"),
        "decisions": os.path.join(ROOT, "decisions.json"),
        "technical": os.path.join(ROOT, "technical.json"),
        "features": os.path.join(ROOT, "features.json"),
        "market": os.path.join(ROOT, "market_state.json"),
        "risk": os.path.join(ROOT, "risk_score.json"),
    }
    payload = build(
        load_json(paths["watch"]),
        load_json(paths["decisions"]),
        load_json(paths["technical"]),
        load_json(paths["features"]),
        load_json(paths["market"]),
        load_json(paths["risk"]),
        previous=load_json(OUTPUT),
    )
    atomic_write(payload)
    print("decision_matrix", payload["summary"])
    for code in payload["ranking"][:5]:
        item = payload["assets"][code]
        print(code, item["name"], item["thesis_state"], item["matrix_direction"], item["composite_score"], item["attention_score"])


if __name__ == "__main__":
    main()
