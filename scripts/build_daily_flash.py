#!/usr/bin/env python3
"""Build the Daily Flash data product from public research artifacts.

This layer is intentionally presentation-oriented: it summarizes market state,
cross-asset context, sector rotation, catalysts, theme states and Decision Matrix
focus without inventing missing values or converting research states into trade
instructions.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "daily_flash.json")
BEIJING = timezone(timedelta(hours=8))

THEMES = [
    ("存储", ["603986", "001309"]),
    ("AI光通信 / CPO", ["300308"]),
    ("PCB / 消费电子", ["002384"]),
    ("半导体工程 / 封测", ["600667"]),
    ("被动元件", ["000636"]),
    ("创新药", ["517380"]),
    ("黄金", ["518880"]),
    ("白银", ["161226"]),
]


def load_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def load_js(path):
    try:
        text = open(path, encoding="utf-8").read()
        return json.loads(text[text.index("{"): text.rindex("}") + 1])
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


def label_from_score(score, pos=15, neg=-15):
    if score is None:
        return "数据不足"
    if score >= pos:
        return "偏多"
    if score <= neg:
        return "偏空"
    return "中性"


def global_map(global_markets):
    return {row.get("key"): row for row in global_markets.get("assets", [])}


def index_rows(market_state):
    rows = market_state.get("indices") or []
    if isinstance(rows, dict):
        rows = list(rows.values())
    output = []
    for row in rows:
        name = row.get("name") or row.get("label") or row.get("code")
        if not name:
            continue
        output.append({
            "name": name,
            "code": row.get("code"),
            "value": row.get("price", row.get("close", row.get("value"))),
            "change_pct": row.get("change_pct"),
            "status": row.get("status", "fresh"),
            "source": row.get("source"),
        })
    return output


def market_metrics(market_state):
    breadth = market_state.get("breadth") or {}
    return {
        "total": breadth.get("total"),
        "up": breadth.get("up"),
        "down": breadth.get("down"),
        "flat": breadth.get("flat"),
        "advance_ratio": breadth.get("advance_ratio"),
        "limit_up": breadth.get("limit_up"),
        "limit_down": breadth.get("limit_down"),
        "touched_limit_up": breadth.get("touched_limit_up"),
        "broken_limit_up": breadth.get("broken_limit_up", breadth.get("broken")),
        "seal_rate": breadth.get("seal_rate"),
        "turnover": breadth.get("turnover"),
        "status": (market_state.get("section_status") or {}).get("breadth", {}).get("status"),
    }


def hs300_valuation(valuation):
    indices = valuation.get("indices") or {}
    for key in ("000300", "沪深300"):
        if key in indices:
            row = indices[key]
            return {
                "pe_ttm": row.get("pe_ttm", row.get("pe")),
                "percentile_10y": row.get("percentile_10y"),
                "band": row.get("band"),
                "status": row.get("status"),
            }
    for row in indices.values():
        if row.get("name") == "沪深300":
            return {
                "pe_ttm": row.get("pe_ttm", row.get("pe")),
                "percentile_10y": row.get("percentile_10y"),
                "band": row.get("band"),
                "status": row.get("status"),
            }
    return {}


def core_conclusion(market_state, risk, valuation, matrix):
    regime = market_state.get("regime") or {}
    breadth = market_state.get("breadth") or {}
    adv = finite(breadth.get("advance_ratio"))
    risk_score = finite(risk.get("score"))
    hs300 = hs300_valuation(valuation)
    leaders = (market_state.get("sectors") or {}).get("leaders") or []
    laggards = (market_state.get("sectors") or {}).get("laggards") or []
    top_codes = (matrix.get("summary") or {}).get("top_attention") or []
    top_names = [matrix.get("assets", {}).get(code, {}).get("name") for code in top_codes[:3]]
    top_names = [name for name in top_names if name]

    parts = [f"A股状态为 {regime.get('label') or regime.get('code') or '数据不足'}"]
    if adv is not None:
        parts.append(f"上涨家数占比 {adv*100:.1f}%")
    if risk_score is not None:
        parts.append(f"风险温度 {risk_score:.0f}/100（{risk.get('label','—')}）")
    sentence1 = "，".join(parts) + "。"

    valuation_bits = []
    if finite(hs300.get("pe_ttm")) is not None:
        valuation_bits.append(f"沪深300 PE-TTM {float(hs300['pe_ttm']):.2f}")
    if finite(hs300.get("percentile_10y")) is not None:
        valuation_bits.append(f"10年分位 {float(hs300['percentile_10y']):.1f}%")
    sector_bits = []
    if leaders:
        sector_bits.append("强势：" + "、".join(str(row.get("name")) for row in leaders[:3] if row.get("name")))
    if laggards:
        sector_bits.append("弱势：" + "、".join(str(row.get("name")) for row in laggards[:3] if row.get("name")))
    sentence2 = "；".join(valuation_bits + sector_bits)
    if sentence2:
        sentence2 += "。"

    sentence3 = ""
    if top_names:
        sentence3 = "研究复核优先关注 " + "、".join(top_names) + "；该排序代表证据变化与复核优先级，不代表交易优先级。"
    return sentence1 + sentence2 + sentence3


def dimension_cards(market_state, risk, globals_):
    gm = global_map(globals_)
    cards = []
    regime_score = finite((market_state.get("regime") or {}).get("score"))
    cards.append({"name": "A股盘面", "score": regime_score, "label": label_from_score(regime_score), "weight": 5, "evidence": f"Market Regime={(market_state.get('regime') or {}).get('code','—')}"})

    us_moves = [finite((gm.get(k) or {}).get("change_pct")) for k in ("sp500", "nasdaq", "sox")]
    us_moves = [x for x in us_moves if x is not None]
    us_score = clamp(sum(us_moves) / len(us_moves) * 20) if us_moves else None
    cards.append({"name": "美股隔夜", "score": round(us_score, 1) if us_score is not None else None, "label": label_from_score(us_score), "weight": 4, "evidence": "标普/纳指/费半平均涨跌" if us_moves else "数据待接入"})

    y10 = finite((gm.get("us10y") or {}).get("change_pct"))
    dxy = finite((gm.get("dxy") or {}).get("change_pct"))
    rates_parts = []
    if y10 is not None:
        rates_parts.append(-y10 * 15)
    if dxy is not None:
        rates_parts.append(-dxy * 20)
    rates_score = clamp(sum(rates_parts) / len(rates_parts)) if rates_parts else None
    cards.append({"name": "美债 / 美元", "score": round(rates_score, 1) if rates_score is not None else None, "label": label_from_score(rates_score), "weight": 5, "evidence": "收益率与美元上行对长久期风险资产偏压制" if rates_parts else "数据待接入"})

    commodity_moves = [finite((gm.get(k) or {}).get("change_pct")) for k in ("gold", "silver", "wti", "brent")]
    commodity_moves = [x for x in commodity_moves if x is not None]
    commodity_score = clamp(sum(commodity_moves) / len(commodity_moves) * 15) if commodity_moves else None
    cards.append({"name": "商品避险", "score": round(commodity_score, 1) if commodity_score is not None else None, "label": label_from_score(commodity_score), "weight": 3, "evidence": "黄金/白银/原油组合变化" if commodity_moves else "数据待接入"})

    overseas_component = finite(((risk.get("components") or {}).get("overseas") or {}).get("score"))
    geo_score = 50 - overseas_component if overseas_component is not None else None
    cards.append({"name": "海外风险", "score": round(geo_score, 1) if geo_score is not None else None, "label": label_from_score(geo_score), "weight": 4, "evidence": "Risk Temperature海外风险分量" if geo_score is not None else "数据待接入"})

    cnh = finite((gm.get("usdcnh") or {}).get("change_pct"))
    fx_score = clamp(-cnh * 25) if cnh is not None else None
    cards.append({"name": "汇率", "score": round(fx_score, 1) if fx_score is not None else None, "label": label_from_score(fx_score), "weight": 3, "evidence": "USD/CNH上行视作人民币走弱压力" if cnh is not None else "数据待接入"})
    return cards


def theme_tracker(matrix):
    assets = matrix.get("assets") or {}
    output = []
    for theme, codes in THEMES:
        items = [assets.get(code) for code in codes if assets.get(code)]
        if not items:
            output.append({"theme": theme, "status": "数据不足", "assets": codes})
            continue
        thesis_states = {item.get("thesis_state") for item in items}
        evidence_states = {item.get("evidence_state") for item in items}
        if "conflicted" in thesis_states or "under_test" in thesis_states or "conflict" in evidence_states:
            status = "证据冲突"
        elif "confirmed" in thesis_states:
            status = "多层确认"
        elif thesis_states.intersection({"supported", "emerging"}):
            status = "方向获支持"
        else:
            status = "等待确认"
        scores = [finite(item.get("composite_score")) for item in items]
        scores = [x for x in scores if x is not None]
        output.append({
            "theme": theme,
            "status": status,
            "assets": codes,
            "names": [item.get("name") for item in items],
            "direction": items[0].get("matrix_direction") if len({item.get("matrix_direction") for item in items}) == 1 else "mixed",
            "score": round(sum(scores) / len(scores), 1) if scores else None,
            "event_score": max([finite((item.get("layers") or {}).get("event", {}).get("score")) for item in items if finite((item.get("layers") or {}).get("event", {}).get("score")) is not None], default=None),
            "technical_score": round(sum([finite((item.get("layers") or {}).get("technical", {}).get("score")) for item in items if finite((item.get("layers") or {}).get("technical", {}).get("score")) is not None]) / max(1, len([1 for item in items if finite((item.get("layers") or {}).get("technical", {}).get("score")) is not None])), 1),
            "industry_score": round(sum([finite((item.get("layers") or {}).get("industry", {}).get("score")) for item in items if finite((item.get("layers") or {}).get("industry", {}).get("score")) is not None]) / max(1, len([1 for item in items if finite((item.get("layers") or {}).get("industry", {}).get("score")) is not None])), 1),
        })
    return output


def key_events(ai):
    rows = ai.get("signals") or []
    output = []
    for row in rows[:10]:
        title = row.get("title") or row.get("event") or row.get("headline") or row.get("summary")
        if not title:
            continue
        output.append({
            "date": row.get("date") or row.get("as_of") or str(ai.get("generated_at") or "")[:10],
            "title": title,
            "impact": row.get("impact") or row.get("reason") or row.get("summary") or row.get("thesis"),
            "direction": row.get("direction") or row.get("bias") or "neutral",
            "strength": row.get("strength") or row.get("score") or row.get("relevance_score"),
            "assets": row.get("assets") or row.get("mapped_assets") or [],
            "source_url": row.get("url") or row.get("source_url"),
        })
    return output[:8]


def outlook(market_state, risk, matrix):
    regime = (market_state.get("regime") or {}).get("code")
    risk_score = finite(risk.get("score"))
    confirmed = (matrix.get("summary") or {}).get("confirmed", 0)
    supported = (matrix.get("summary") or {}).get("supported", 0)
    bullish = "若上涨占比重新站上50%、Market Regime转向risk_on/narrow_risk_on，且强势主题的行业与技术层同步扩散，则风险偏好修复更可信。"
    bearish = "若市场广度继续恶化、风险温度抬升，同时当前获支持主题转为conflict/contradicted，则应把环境定义为进一步收缩而非普通波动。"
    base = f"当前基准情景：regime={regime or '—'}，风险温度={risk_score if risk_score is not None else '—'}；Matrix中 confirmed={confirmed}、supported={supported}。"
    return {"base": base, "bullish": bullish, "bearish": bearish}


def matrix_focus(matrix):
    assets = matrix.get("assets") or {}
    result = []
    for code in matrix.get("ranking", [])[:6]:
        item = assets.get(code) or {}
        result.append({
            "code": code,
            "name": item.get("name"),
            "thesis_state": item.get("thesis_state"),
            "direction": item.get("matrix_direction"),
            "attention_score": item.get("attention_score"),
            "composite_score": item.get("composite_score"),
            "confluence": item.get("confluence"),
            "conflict_score": item.get("conflict_score"),
            "focus": item.get("research_focus"),
        })
    return result


def build(inputs, now=None):
    now = now or datetime.now(BEIJING)
    market_state = inputs.get("market_state", {})
    risk = inputs.get("risk", {})
    valuation = inputs.get("valuation", {})
    matrix = inputs.get("matrix", {})
    globals_ = inputs.get("global", {})
    catalysts = inputs.get("catalysts", {})
    ai = inputs.get("ai", {})
    sectors = market_state.get("sectors") or {}
    flows = market_state.get("industry_flow") or {}
    return {
        "version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "title": "Daily Flash · 每日投资驾驶舱",
        "core_conclusion": core_conclusion(market_state, risk, valuation, matrix),
        "market": {
            "regime": market_state.get("regime"),
            "risk": {"score": risk.get("score"), "label": risk.get("label"), "coverage": risk.get("coverage")},
            "valuation_hs300": hs300_valuation(valuation),
            "indices": index_rows(market_state),
            "metrics": market_metrics(market_state),
        },
        "sector_rotation": {
            "leaders": (sectors.get("leaders") or [])[:6],
            "laggards": (sectors.get("laggards") or [])[:6],
            "inflow": (flows.get("inflow") or [])[:6],
            "outflow": (flows.get("outflow") or [])[:6],
        },
        "global_markets": globals_.get("assets", []),
        "key_events": key_events(ai),
        "catalysts": (catalysts.get("events") or [])[:20],
        "dimensions": dimension_cards(market_state, risk, globals_),
        "themes": theme_tracker(matrix),
        "outlook": outlook(market_state, risk, matrix),
        "matrix_focus": matrix_focus(matrix),
        "sources": {
            "market_state": market_state.get("generated_at"),
            "risk": risk.get("generated_at"),
            "valuation": valuation.get("generated_at"),
            "decision_matrix": matrix.get("generated_at"),
            "global_markets": globals_.get("generated_at"),
            "catalysts": catalysts.get("generated_at"),
            "ai_signals": ai.get("generated_at"),
        },
        "boundary": "Daily Flash用于信息压缩、研究排序与条件验证；缺失数据保持缺失，不生成无条件买卖、仓位或止损指令。",
    }


def main():
    inputs = {
        "market_state": load_json(os.path.join(ROOT, "market_state.json")),
        "risk": load_json(os.path.join(ROOT, "risk_score.json")),
        "valuation": load_json(os.path.join(ROOT, "valuation.json")),
        "matrix": load_json(os.path.join(ROOT, "decision_matrix.json")),
        "global": load_json(os.path.join(ROOT, "global_markets.json")),
        "catalysts": load_json(os.path.join(ROOT, "catalysts.json")),
        "ai": load_js(os.path.join(ROOT, "ai-signals.js")),
    }
    payload = build(inputs)
    tmp = OUTPUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(tmp, OUTPUT)
    print("daily flash", payload["generated_at"], "events", len(payload["key_events"]), "catalysts", len(payload["catalysts"]))


if __name__ == "__main__":
    main()
