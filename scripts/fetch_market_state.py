#!/usr/bin/env python3
"""Build a failure-tolerant A-share market-state snapshot.

Adds public market context beside watchlist quotes: breadth, core indices,
sector leaders/laggards, industry fund-flow when explicitly available, and an
ETF turnover activity proxy. Missing upstream data is never fabricated.
"""

from __future__ import annotations

import json
import math
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTPUT = os.path.join(ROOT, "market_state.json")
BEIJING = timezone(timedelta(hours=8))

INDEX_TAPE = [
    ("sh000001", "上证指数"), ("sz399001", "深证成指"),
    ("sz399006", "创业板指"), ("sh000688", "科创50"),
    ("sh000300", "沪深300"), ("sh000905", "中证500"),
    ("hkHSI", "恒生指数"), ("hkHSTECH", "恒生科技"),
]


def finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def rounded(value, digits=4):
    return round(value, digits) if value is not None and math.isfinite(value) else None


def load_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def atomic_write(payload, path=OUTPUT):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(tmp, path)


def _first(row, *names):
    for name in names:
        if name in row and row.get(name) not in (None, ""):
            return row.get(name)
    return None


def _to_records(frame):
    if frame is None or getattr(frame, "empty", True):
        return []
    return [row.to_dict() for _, row in frame.iterrows()]


def daily_limit_pct(code, name):
    code = str(code or "")
    name = str(name or "").upper()
    if "ST" in name:
        return 5.0
    if code.startswith(("300", "301", "688", "689")):
        return 20.0
    if code.startswith(("4", "8")):
        return 30.0
    return 10.0


def breadth_from_rows(rows):
    total = up = down = flat = limit_up = limit_down = touched_up = broken_up = 0
    turnover = 0.0
    turnover_count = 0
    for row in rows:
        code = str(_first(row, "代码", "code") or "")
        name = str(_first(row, "名称", "name") or "")
        pct = finite(_first(row, "涨跌幅", "change_pct"))
        price = finite(_first(row, "最新价", "price"))
        high = finite(_first(row, "最高", "high"))
        prev = finite(_first(row, "昨收", "previous_close"))
        amount = finite(_first(row, "成交额", "turnover", "amount"))
        if pct is None:
            continue
        total += 1
        if pct > 0.01:
            up += 1
        elif pct < -0.01:
            down += 1
        else:
            flat += 1
        if amount is not None and amount >= 0:
            turnover += amount
            turnover_count += 1

        band = daily_limit_pct(code, name)
        at_up = pct >= band - 0.35
        at_down = pct <= -band + 0.35
        hit_up = high is not None and prev not in (None, 0) and high / prev - 1 >= band / 100 - 0.0035
        limit_up += int(at_up)
        limit_down += int(at_down)
        if hit_up:
            touched_up += 1
            broken_up += int(not at_up and price is not None)

    adv = up / total if total else None
    seal = limit_up / touched_up if touched_up else None
    return {
        "total": total, "up": up, "down": down, "flat": flat,
        "advance_ratio": rounded(adv),
        "limit_up": limit_up, "limit_down": limit_down,
        "touched_limit_up": touched_up, "broken_limit_up": broken_up,
        "seal_rate": rounded(seal),
        "turnover": round(turnover, 2) if turnover_count else None,
        "turnover_coverage": rounded(turnover_count / total) if total else None,
    }


def parse_tencent_indices(text, requested=INDEX_TAPE):
    names = dict(requested)
    rows = []
    for match in re.finditer(r'v_([^=]+)="([^"]*)";', text):
        symbol, raw = match.groups()
        if symbol not in names:
            continue
        fields = raw.split("~")
        if len(fields) < 5:
            continue
        price = finite(fields[3])
        previous = finite(fields[4])
        pct = finite(fields[32]) if len(fields) > 32 else None
        if pct is None and price is not None and previous not in (None, 0):
            pct = (price / previous - 1) * 100
        rows.append({
            "symbol": symbol, "name": fields[1] or names[symbol],
            "price": rounded(price, 3), "change_pct": rounded(pct, 2),
            "source": "腾讯行情",
        })
    order = {symbol: i for i, (symbol, _) in enumerate(requested)}
    rows.sort(key=lambda row: order.get(row["symbol"], 999))
    return rows


def fetch_tencent_indices():
    symbols = [symbol for symbol, _ in INDEX_TAPE]
    url = "https://qt.gtimg.cn/q=" + urllib.parse.quote(",".join(symbols), safe=",")
    req = urllib.request.Request(url, headers={"User-Agent": "investment-news/2.0"})
    with urllib.request.urlopen(req, timeout=12) as response:
        rows = parse_tencent_indices(response.read().decode("gbk", errors="ignore"))
    if len(rows) < 4:
        raise RuntimeError(f"Tencent returned only {len(rows)} usable indices")
    return rows


def normalize_sector_rows(frame, limit=8):
    rows = []
    for row in _to_records(frame):
        name = _first(row, "板块名称", "名称")
        pct = finite(_first(row, "涨跌幅", "今日涨跌幅"))
        if not name or pct is None:
            continue
        rows.append({
            "name": str(name), "change_pct": rounded(pct, 2),
            "leader": _first(row, "领涨股票", "领涨股"),
            "source": "东方财富 via AKShare",
        })
    rows.sort(key=lambda x: x["change_pct"], reverse=True)
    return {"leaders": rows[:limit], "laggards": list(reversed(rows[-limit:])), "coverage": len(rows)}


def _find_numeric(row, tokens):
    for key, value in row.items():
        if all(token in str(key) for token in tokens):
            number = finite(value)
            if number is not None:
                return number
    return None


def normalize_flow_rows(frame, limit=8):
    rows = []
    for row in _to_records(frame):
        name = _first(row, "名称", "板块名称")
        net = _find_numeric(row, ("主力", "净流入", "净额"))
        if net is None:
            net = finite(_first(row, "主力净流入-净额", "今日主力净流入-净额", "主力净流入"))
        if not name or net is None:
            continue
        rows.append({
            "name": str(name), "net_inflow": rounded(net, 2),
            "change_pct": rounded(finite(_first(row, "今日涨跌幅", "涨跌幅")), 2),
            "source": "东方财富 via AKShare",
        })
    rows.sort(key=lambda x: x["net_inflow"], reverse=True)
    return {"inflow": rows[:limit], "outflow": list(reversed(rows[-limit:])), "coverage": len(rows)}


def normalize_etf_activity(frame, limit=12):
    rows = []
    exclude = ("货币", "现金", "短融", "同业存单", "国债", "债券", "政金债")
    for row in _to_records(frame):
        name = str(_first(row, "名称", "name") or "")
        if not name or any(token in name for token in exclude):
            continue
        amount = finite(_first(row, "成交额", "turnover", "amount"))
        if amount is None or amount <= 0:
            continue
        rows.append({
            "code": str(_first(row, "代码", "code") or "").zfill(6),
            "name": name,
            "price": rounded(finite(_first(row, "最新价", "price")), 3),
            "change_pct": rounded(finite(_first(row, "涨跌幅", "change_pct")), 2),
            "turnover": round(amount, 2),
            "metric": "成交额活跃度代理",
            "source": "东方财富 via AKShare",
        })
    rows.sort(key=lambda x: x["turnover"], reverse=True)
    return rows[:limit]


def score_regime(breadth, indices):
    adv = finite(breadth.get("advance_ratio"))
    idx = [finite(row.get("change_pct")) for row in indices]
    idx = [value for value in idx if value is not None]
    if adv is None and not idx:
        return {"label": "数据不足", "code": "insufficient", "score": None, "components": {}}

    # Important: 0.0 is a valid breadth reading, not a missing value.
    adv_for_score = 0.5 if adv is None else adv
    breadth_score = max(-1.0, min(1.0, (adv_for_score - 0.5) * 2.5))
    index_mean = sum(idx) / len(idx) if idx else 0.0
    index_score = max(-1.0, min(1.0, index_mean / 1.5))
    up = int(breadth.get("limit_up") or 0)
    down = int(breadth.get("limit_down") or 0)
    limit_score = (up - down) / (up + down) if up + down else 0.0
    score = 0.55 * breadth_score + 0.30 * index_score + 0.15 * limit_score

    if score >= 0.35 and adv is not None and adv >= 0.60:
        code, label = "risk_on", "Risk-on"
    elif score >= 0.12:
        code, label = "narrow_risk_on", "Narrow Risk-on"
    elif score <= -0.35 and adv is not None and adv <= 0.40:
        code, label = "risk_off", "Risk-off"
    else:
        code, label = "transition", "Transition"
    return {
        "label": label, "code": code, "score": rounded(score * 100, 1),
        "components": {
            "breadth": rounded(breadth_score * 100, 1),
            "indices": rounded(index_score * 100, 1),
            "limit_structure": rounded(limit_score * 100, 1),
        },
        "methodology": "市场广度55% + 核心指数30% + 涨跌停结构15%；仅用于状态分类，不是收益概率。",
    }


def state_alerts(previous, current):
    alerts = []
    old = (previous.get("regime") or {}).get("code")
    new = (current.get("regime") or {}).get("code")
    if old and new and old != new:
        alerts.append({"type": "regime", "from": old, "to": new, "message": f"市场状态由 {old} 切换为 {new}"})
    old_adv = finite((previous.get("breadth") or {}).get("advance_ratio"))
    new_adv = finite((current.get("breadth") or {}).get("advance_ratio"))
    for threshold, name in ((0.35, "弱势阈值"), (0.50, "多空中轴"), (0.65, "强势阈值")):
        if old_adv is None or new_adv is None:
            continue
        if (old_adv < threshold <= new_adv) or (old_adv >= threshold > new_adv):
            direction = "上穿" if new_adv >= threshold else "下穿"
            alerts.append({"type": "breadth", "threshold": threshold, "message": f"上涨家数占比{direction}{name} {threshold:.0%}"})
    return alerts[:8]


def preserve_section(previous, key, error):
    value = previous.get(key)
    if value not in (None, {}, []):
        return value, {"status": "stale", "error": str(error)[:240]}
    return None, {"status": "unavailable", "error": str(error)[:240]}


def build_payload(previous=None, now=None, a_share_rows=None, indices=None, sectors=None, industry_flow=None, etf_activity=None):
    previous = previous or {}
    now = now or datetime.now(BEIJING)
    status = {}

    if a_share_rows is None:
        breadth, status["breadth"] = preserve_section(previous, "breadth", "A-share breadth unavailable")
    else:
        breadth = breadth_from_rows(a_share_rows)
        status["breadth"] = {"status": "fresh" if breadth.get("total") else "unavailable"}

    def section(key, value, empty):
        if value is None:
            kept, state = preserve_section(previous, key, f"{key} unavailable")
            return kept if kept is not None else empty, state
        usable = bool(value.get("coverage")) if isinstance(value, dict) and "coverage" in value else bool(value)
        return value, {"status": "fresh" if usable else "unavailable"}

    indices, status["indices"] = section("indices", indices, [])
    sectors, status["sectors"] = section("sectors", sectors, {"leaders": [], "laggards": [], "coverage": 0})
    industry_flow, status["industry_flow"] = section("industry_flow", industry_flow, {"inflow": [], "outflow": [], "coverage": 0})
    etf_activity, status["etf_activity"] = section("etf_activity", etf_activity, [])
    breadth = breadth or {}

    payload = {
        "version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "breadth": breadth,
        "indices": indices,
        "sectors": sectors,
        "industry_flow": industry_flow,
        "etf_activity": etf_activity,
        "regime": score_regime(breadth, indices),
        "section_status": status,
        "warnings": [],
        "methodology": {
            "breadth": "全A实时快照计算上涨/下跌/平盘、涨跌停触及与封板率；涨跌停阈值按板块/ST规则近似。",
            "industry_flow": "仅在数据源提供明确主力净流入字段时展示。",
            "etf_activity": "ETF成交额活跃度代理，不等同ETF净申购或真实资金净流入。",
        },
    }
    payload["alerts"] = state_alerts(previous, payload)
    return payload


def fetch_live(previous=None, now=None):
    import akshare as ak

    previous = previous or {}
    now = now or datetime.now(BEIJING)
    warnings = []

    def attempt(label, fn):
        try:
            return fn()
        except Exception as exc:
            warnings.append(f"{label}: {exc}")
            return None

    a_share_rows = attempt("breadth", lambda: _to_records(ak.stock_zh_a_spot_em()))
    indices = attempt("indices", fetch_tencent_indices)
    sectors = attempt("sectors", lambda: normalize_sector_rows(ak.stock_board_industry_name_em()))
    industry_flow = attempt(
        "industry_flow",
        lambda: normalize_flow_rows(ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")),
    )
    etf_activity = attempt("etf_activity", lambda: normalize_etf_activity(ak.fund_etf_spot_em()))

    payload = build_payload(previous, now, a_share_rows, indices, sectors, industry_flow, etf_activity)
    payload["warnings"].extend(warnings)
    return payload


def main():
    payload = fetch_live(load_json(OUTPUT))
    atomic_write(payload)
    print("market_state", payload["regime"], payload.get("breadth", {}))
    for warning in payload["warnings"]:
        print("warning:", warning)


if __name__ == "__main__":
    main()
