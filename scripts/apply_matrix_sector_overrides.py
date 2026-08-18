#!/usr/bin/env python3
"""Apply narrow, asset-specific sector mappings to Decision Matrix industry layer.

`watchlist.industries` remains a broad taxonomy for news discovery. The optional
`matrix_sectors` field is deliberately narrower and is used only for market
validation, preventing unrelated taxonomy branches from diluting or contaminating
industry evidence.
"""

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "decision_matrix.json")


def load(path):
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


def clamp(value, low=-100.0, high=100.0):
    return max(low, min(high, float(value)))


def rounded(value, digits=1):
    return round(float(value), digits) if value is not None else None


def observed_sectors(market_state):
    rows = {}
    for key in ("leaders", "laggards"):
        for row in (market_state.get("sectors") or {}).get(key, []) or []:
            name = str(row.get("name") or "")
            if not name:
                continue
            slot = rows.setdefault(name, {})
            slot["change_pct"] = finite(row.get("change_pct"))
            slot["source"] = row.get("source")
    for key in ("inflow", "outflow"):
        for row in (market_state.get("industry_flow") or {}).get(key, []) or []:
            name = str(row.get("name") or "")
            if not name:
                continue
            slot = rows.setdefault(name, {})
            if finite(row.get("change_pct")) is not None:
                slot["change_pct"] = finite(row.get("change_pct"))
            slot["net_inflow"] = finite(row.get("net_inflow"))
            slot["source"] = row.get("source") or slot.get("source")
    return rows


def exact_industry_layer(sectors, market_state):
    sectors = list(dict.fromkeys(str(x) for x in (sectors or []) if str(x)))
    if not sectors:
        return {
            "available": False,
            "score": None,
            "confidence": "none",
            "evidence": "该标的未配置 Decision Matrix 行业代理；行业层不参与合成。",
            "matches": [],
            "mapping_mode": "explicit_none",
        }
    observed = observed_sectors(market_state)
    matches = [(name, observed[name]) for name in sectors if name in observed]
    if not matches:
        return {
            "available": False,
            "score": None,
            "confidence": "none",
            "evidence": "配置的精准行业未进入当前强弱/资金榜；缺失不按中性处理。",
            "matches": [],
            "configured_sectors": sectors,
            "mapping_mode": "explicit",
        }

    scored, details = [], []
    for name, row in matches:
        pct = finite(row.get("change_pct"))
        flow = finite(row.get("net_inflow"))
        pieces = []
        if pct is not None:
            pieces.append((0.45, clamp(pct / 3.0 * 100)))
        if flow is not None:
            pieces.append((0.55, math.tanh(flow / 20_000_000_000) * 100))
        if not pieces:
            continue
        denom = sum(weight for weight, _ in pieces)
        score = sum(weight * value for weight, value in pieces) / denom
        scored.append(score)
        pct_text = f"{pct:+.2f}%" if pct is not None else "—"
        flow_text = f"{flow / 1e8:.1f}亿" if flow is not None else "—"
        details.append(f"{name} 涨跌{pct_text}/净流{flow_text}")

    if not scored:
        return {
            "available": False,
            "score": None,
            "confidence": "none",
            "evidence": "精准行业有观测名称但无可用数值。",
            "matches": [],
            "configured_sectors": sectors,
            "mapping_mode": "explicit",
        }
    return {
        "available": True,
        "score": rounded(clamp(sum(scored) / len(scored))),
        "confidence": "medium" if len(scored) >= 2 else "low",
        "evidence": "；".join(details),
        "matches": [name for name, _ in matches],
        "configured_sectors": sectors,
        "mapping_mode": "explicit",
    }


def apply(matrix, watchlist, market_state):
    asset_map = {str(asset.get("code")): asset for asset in watchlist.get("assets", [])}
    changes = []
    for code, item in (matrix.get("assets") or {}).items():
        asset = asset_map.get(str(code), {})
        if "matrix_sectors" not in asset:
            continue
        before = (item.get("layers") or {}).get("industry", {})
        after = exact_industry_layer(asset.get("matrix_sectors"), market_state)
        item.setdefault("layers", {})["industry"] = after
        changes.append({
            "code": str(code),
            "name": item.get("name"),
            "configured_sectors": asset.get("matrix_sectors"),
            "before_matches": before.get("matches", []),
            "after_matches": after.get("matches", []),
        })
    matrix.setdefault("methodology", {})["sector_mapping"] = (
        "新闻 industries 用于高召回事件发现；Decision Matrix 优先使用 watchlist.matrix_sectors 精准行业代理，"
        "避免将同一新闻 taxonomy 的所有相邻行业都当成价格验证证据。"
    )
    matrix["sector_mapping_audit"] = changes
    return matrix


def main():
    matrix = load(OUTPUT)
    watchlist = load(os.path.join(ROOT, "watchlist.json"))
    market_state = load(os.path.join(ROOT, "market_state.json"))
    payload = apply(matrix, watchlist, market_state)
    temporary = OUTPUT + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, OUTPUT)
    print("matrix sector overrides", len(payload.get("sector_mapping_audit", [])))


if __name__ == "__main__":
    main()
