#!/usr/bin/env python3
"""Refine Decision Matrix conflict, freshness and evidence eligibility semantics.

The base engine computes transparent layer scores. This pass then enforces two
additional rules before final classification:
1) stale evidence is not allowed to masquerade as current directional evidence;
2) economically irrelevant cross-market proxies are excluded (for example,
   A-share energy sectors are not treated as a gold/silver industry signal).

After exclusions the composite is recomputed with the remaining fixed weights.
Missing/excluded layers are renormalized, never silently replaced with zero.
"""

from __future__ import annotations

import argparse
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "decision_matrix.json")
WEIGHTS = {
    "event": 25,
    "technical": 30,
    "relative_strength": 20,
    "industry": 15,
    "market_context": 10,
}
HEDGE_GROUPS = {"贵金属对冲"}


def load(path):
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


def rounded(value, digits=1):
    return round(float(value), digits) if value is not None and math.isfinite(float(value)) else None


def sign(value, threshold=15.0):
    value = finite(value)
    if value is None or abs(value) < threshold:
        return 0
    return 1 if value > 0 else -1


def exclude_layer(layer, reason):
    layer["available"] = False
    layer["score"] = None
    layer["confidence"] = "none"
    layer["evidence"] = reason
    if "matches" in layer:
        layer["matches"] = []


def apply_eligibility(item, market_state=None, technical=None, features=None):
    """Fail closed when a layer is stale or economically inapplicable."""
    excluded = []
    layers = item.get("layers") or {}
    code = str(item.get("code"))

    if item.get("group") in HEDGE_GROUPS:
        layer = layers.get("industry")
        if layer and layer.get("available"):
            reason = "贵金属对冲不使用A股能源/行业板块作为方向证据。"
            exclude_layer(layer, reason)
            excluded.append({"layer": "industry", "reason": reason})

    if market_state:
        status = market_state.get("section_status") or {}
        sector_fresh = (status.get("sectors") or {}).get("status") == "fresh"
        flow_fresh = (status.get("industry_flow") or {}).get("status") == "fresh"
        layer = layers.get("industry")
        if layer and layer.get("available") and not (sector_fresh or flow_fresh):
            reason = "行业强弱与行业资金均非 fresh；该层暂不参与当前矩阵。"
            exclude_layer(layer, reason)
            excluded.append({"layer": "industry", "reason": reason})

        breadth_fresh = (status.get("breadth") or {}).get("status") == "fresh"
        indices_fresh = (status.get("indices") or {}).get("status") == "fresh"
        layer = layers.get("market_context")
        if layer and layer.get("available") and not (breadth_fresh and indices_fresh):
            reason = "市场广度或核心指数非 fresh；环境层暂不参与当前矩阵。"
            exclude_layer(layer, reason)
            excluded.append({"layer": "market_context", "reason": reason})

    if technical:
        raw = (technical.get("assets") or {}).get(code)
        layer = layers.get("technical")
        if layer and layer.get("available") and (
            not raw or raw.get("source_status") != "fresh" or raw.get("data_quality") != "usable"
        ):
            reason = "技术源数据非 fresh/usable；技术层暂不参与当前矩阵。"
            exclude_layer(layer, reason)
            excluded.append({"layer": "technical", "reason": reason})

    if features:
        raw = (features.get("assets") or {}).get(code)
        layer = layers.get("relative_strength")
        if layer and layer.get("available") and (not raw or raw.get("status") != "fresh"):
            reason = "相对强弱源数据非 fresh；该层暂不参与当前矩阵。"
            exclude_layer(layer, reason)
            excluded.append({"layer": "relative_strength", "reason": reason})

    item["excluded_layers"] = excluded
    return excluded


def recombine(item):
    layers = item.get("layers") or {}
    available = [
        (name, layer, WEIGHTS[name])
        for name, layer in layers.items()
        if name in WEIGHTS and layer.get("available") and finite(layer.get("score")) is not None
    ]
    available_weight = sum(weight for _, _, weight in available)
    if not available_weight:
        item["composite_score"] = None
        item["coverage"] = 0.0
        item["confluence"] = 0.0
        item["available_layers"] = 0
        item["opposing_weight_share"] = 0.0
        item["matrix_direction"] = "insufficient"
        return item

    composite = sum(weight * float(layer["score"]) for _, layer, weight in available) / available_weight
    coverage = available_weight / sum(WEIGHTS.values()) * 100.0
    direction = "bullish" if composite >= 20 else "bearish" if composite <= -20 else "neutral"
    direction_sign = 1 if direction == "bullish" else -1 if direction == "bearish" else 0
    directional = [(name, layer, weight) for name, layer, weight in available if sign(layer.get("score"))]

    if direction_sign and directional:
        directional_weight = sum(weight for _, _, weight in directional)
        agree_weight = sum(weight for _, layer, weight in directional if sign(layer.get("score")) == direction_sign)
        agreement = agree_weight / directional_weight * 100.0 if directional_weight else 0.0
        confluence = min(100.0, agreement * 0.7 + abs(composite) * 0.3)
        opposing_weight = sum(weight for _, layer, weight in directional if sign(layer.get("score")) == -direction_sign)
        opposing_share = opposing_weight / available_weight * 100.0
    else:
        confluence = min(45.0, abs(composite) * 1.5)
        opposing_share = 0.0

    item["composite_score"] = rounded(composite)
    item["coverage"] = rounded(coverage)
    item["confluence"] = rounded(confluence)
    item["available_layers"] = len(available)
    item["opposing_weight_share"] = rounded(opposing_share)
    item["matrix_direction"] = direction
    return item


def conflict_metrics(layers):
    """Return magnitude-aware positive/negative evidence balance."""
    positive_mass = 0.0
    negative_mass = 0.0
    positive_weight = 0.0
    negative_weight = 0.0
    for name, layer in (layers or {}).items():
        if name not in WEIGHTS or not layer.get("available"):
            continue
        score = finite(layer.get("score"))
        if score is None or abs(score) < 15:
            continue
        weight = float(WEIGHTS[name])
        mass = weight * min(abs(score), 100.0) / 100.0
        if score > 0:
            positive_mass += mass
            positive_weight += weight
        else:
            negative_mass += mass
            negative_weight += weight

    total_mass = positive_mass + negative_mass
    if positive_mass > 0 and negative_mass > 0 and total_mass > 0:
        balance = 2.0 * min(positive_mass, negative_mass) / total_mass * 100.0
        smaller = min(positive_mass, negative_mass)
        materiality = min(1.0, smaller / 3.0)
        conflict_score = balance * materiality
    else:
        conflict_score = 0.0

    return {
        "positive_mass": rounded(positive_mass),
        "negative_mass": rounded(negative_mass),
        "positive_weight": rounded(positive_weight),
        "negative_weight": rounded(negative_weight),
        "conflict_score": rounded(conflict_score),
    }


def refined_evidence_state(item, metrics):
    direction = item.get("matrix_direction")
    composite = finite(item.get("composite_score"))
    confluence = finite(item.get("confluence")) or 0.0
    coverage = finite(item.get("coverage")) or 0.0
    layer_count = int(item.get("available_layers") or 0)
    opposing_share = finite(item.get("opposing_weight_share")) or 0.0
    conflict = finite(metrics.get("conflict_score")) or 0.0
    smaller_mass = min(finite(metrics.get("positive_mass")) or 0.0, finite(metrics.get("negative_mass")) or 0.0)

    if layer_count < 3 or coverage < 50:
        return "insufficient"
    if direction == "neutral":
        if conflict >= 55 and smaller_mass >= 3:
            return "conflict"
        return "noise_or_no_edge"
    if direction not in {"bullish", "bearish"}:
        return "insufficient"
    if opposing_share >= 30 or (conflict >= 70 and smaller_mass >= 4):
        return "conflict"
    if confluence >= 72 and abs(composite or 0.0) >= 38:
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
        if evidence == "conflict":
            return "conflicted"
        return "supported"
    if direction == "neutral":
        return "under_test" if evidence != "conflict" else "conflicted"
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
    if thesis == "conflicted" or evidence == "conflict":
        return "正负证据正在相互抵消，优先识别哪一层先失效或被确认。"
    if thesis == "under_test":
        return "原方向尚未被市场充分确认，继续观察验证/失效条件。"
    if thesis == "emerging":
        return "出现新方向，但先等待事件或行业证据确认。"
    if evidence == "noise_or_no_edge":
        return "当前缺少足够方向性证据，维持低优先级观察。"
    return "数据或证据覆盖不足，先补齐关键层。"


def attention_score(thesis, evidence, confluence, priority, conflict_score):
    base = {
        "contradicted": 92,
        "conflicted": 82,
        "under_test": 68,
        "confirmed": 62,
        "emerging": 60,
        "supported": 52,
        "no_directional_thesis": 35,
    }.get(thesis, 40)
    if evidence == "insufficient":
        base = max(base, 55)
    base += max(0, min(10, (priority or 3) * 2 - 4))
    base += min(8, (confluence or 0) / 15)
    if evidence == "conflict":
        base += min(6, (conflict_score or 0) / 20)
    return rounded(min(100, base))


def refine(payload, previous=None, market_state=None, technical=None, features=None):
    previous = previous or {}
    old_assets = previous.get("assets", {})
    changes = list(payload.get("state_changes") or [])
    assets = payload.get("assets", {})

    for code, item in assets.items():
        apply_eligibility(item, market_state, technical, features)
        recombine(item)
        metrics = conflict_metrics(item.get("layers", {}))
        evidence = refined_evidence_state(item, metrics)
        thesis = thesis_state(item.get("base_bias"), item.get("matrix_direction"), evidence)
        item["positive_direction_mass"] = metrics["positive_mass"]
        item["negative_direction_mass"] = metrics["negative_mass"]
        item["conflict_score"] = metrics["conflict_score"]
        item["evidence_state"] = evidence
        item["thesis_state"] = thesis
        item["research_focus"] = research_focus(thesis, evidence)
        item["attention_score"] = attention_score(
            thesis,
            evidence,
            finite(item.get("confluence")) or 0.0,
            item.get("priority"),
            metrics["conflict_score"],
        )

        old = old_assets.get(code, {})
        for field in ("matrix_direction", "evidence_state", "thesis_state"):
            before, after = old.get(field), item.get(field)
            if before and after and before != after:
                change = {"code": code, "name": item.get("name"), "field": field, "from": before, "to": after}
                if change not in changes:
                    changes.append(change)

    ordered = sorted(
        assets.values(),
        key=lambda x: (-float(x.get("attention_score") or 0), -int(x.get("priority") or 0), x.get("name") or ""),
    )
    payload["ranking"] = [item["code"] for item in ordered]
    payload["summary"] = {
        "total": len(assets),
        "confirmed": sum(item.get("thesis_state") == "confirmed" for item in assets.values()),
        "supported": sum(item.get("thesis_state") == "supported" for item in assets.values()),
        "contradicted": sum(item.get("thesis_state") == "contradicted" for item in assets.values()),
        "conflicted": sum(item.get("thesis_state") in {"conflicted", "under_test"} for item in assets.values()),
        "emerging": sum(item.get("thesis_state") == "emerging" for item in assets.values()),
        "insufficient": sum(item.get("evidence_state") == "insufficient" for item in assets.values()),
        "top_attention": [item["code"] for item in ordered[:5]],
    }
    payload["state_changes"] = changes[:30]
    methodology = payload.setdefault("methodology", {})
    methodology["eligibility"] = (
        "只有 fresh/usable 的技术、相对强弱和市场/行业数据才能作为当前方向证据；"
        "贵金属对冲明确排除A股行业与A股市场环境方向层。被排除层不按0处理，而是重新归一剩余权重。"
    )
    methodology["conflict"] = (
        "方向层按 固定权重×|score| 形成正负证据质量；只有两侧均达到材料性阈值且较平衡时才标记 conflict，"
        "用于区分‘证据互相抵消’与‘单纯无边际’。conflict_score 不是收益概率。"
    )
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", default=None)
    args = parser.parse_args()
    current = load(OUTPUT)
    previous = load(args.previous) if args.previous else {}
    refined = refine(
        current,
        previous,
        market_state=load(os.path.join(ROOT, "market_state.json")),
        technical=load(os.path.join(ROOT, "technical.json")),
        features=load(os.path.join(ROOT, "features.json")),
    )
    atomic_write(refined)
    print("refined decision matrix", refined.get("summary"))
    for code in refined.get("ranking", [])[:5]:
        item = refined["assets"][code]
        print(
            code,
            item.get("name"),
            item.get("thesis_state"),
            item.get("evidence_state"),
            "score", item.get("composite_score"),
            "conflict", item.get("conflict_score"),
            "excluded", len(item.get("excluded_layers") or []),
        )


if __name__ == "__main__":
    main()
