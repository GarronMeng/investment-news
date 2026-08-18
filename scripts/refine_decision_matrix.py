#!/usr/bin/env python3
"""Refine Decision Matrix conflict semantics without changing base layer scores.

A near-zero composite can mean either genuine lack of edge or cancellation between
material positive and negative evidence. This pass separates those cases using
weighted directional evidence mass. It never changes underlying layer scores and
never emits trading instructions.
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


def conflict_metrics(layers):
    """Return magnitude-aware positive/negative evidence balance.

    Each material layer contributes weight * abs(score)/100. Scores with
    absolute value below 15 are treated as non-directional. conflict_score is
    high only when both sides have meaningful mass and are reasonably balanced.
    """
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


def refine(payload, previous=None):
    previous = previous or {}
    old_assets = previous.get("assets", {})
    changes = list(payload.get("state_changes") or [])
    assets = payload.get("assets", {})

    for code, item in assets.items():
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
    refined = refine(current, previous)
    atomic_write(refined)
    print("refined decision matrix", refined.get("summary"))
    for code in refined.get("ranking", [])[:5]:
        item = refined["assets"][code]
        print(code, item.get("name"), item.get("thesis_state"), item.get("evidence_state"), "conflict", item.get("conflict_score"))


if __name__ == "__main__":
    main()
