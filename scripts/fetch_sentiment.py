#!/usr/bin/env python3
"""Build a small, source-aware sentiment data layer for the dashboard.

OpenBB is the primary adapter for VIX. AKShare wraps the official SSE/SZSE
margin endpoints. Every metric carries freshness and confidence metadata; a
failed refresh keeps the last successful value and marks it stale.
"""

from __future__ import annotations

import json
import math
import os
import statistics
import asyncio
import csv
import io
import urllib.request
from datetime import date, datetime, timedelta, timezone


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTPUT = os.path.join(ROOT, "sentiment.json")
BEIJING = timezone(timedelta(hours=8))
LOOKBACK_DAYS = 45
MIN_OBSERVATIONS = 20


def finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def pct_change(current, previous):
    current, previous = finite(current), finite(previous)
    if current is None or previous in (None, 0):
        return None
    return round((current / previous - 1) * 100, 2)


def percentile_rank(values, current=None):
    cleaned = [number for value in values if (number := finite(value)) is not None]
    current = finite(current if current is not None else (cleaned[-1] if cleaned else None))
    if not cleaned or current is None:
        return None
    return round(sum(value <= current for value in cleaned) / len(cleaned) * 100, 1)


def zscore(values, current=None):
    cleaned = [number for value in values if (number := finite(value)) is not None]
    current = finite(current if current is not None else (cleaned[-1] if cleaned else None))
    if len(cleaned) < 2 or current is None:
        return None
    deviation = statistics.pstdev(cleaned)
    if deviation == 0:
        return 0.0
    return round((current - statistics.mean(cleaned)) / deviation, 2)


def age_days(as_of, today=None):
    today = today or datetime.now(BEIJING).date()
    try:
        observed = date.fromisoformat(str(as_of)[:10])
    except (TypeError, ValueError):
        return None
    return max(0, (today - observed).days)


def freshness(as_of, max_age_days, today=None):
    lag = age_days(as_of, today=today)
    return ("fresh" if lag is not None and lag <= max_age_days else "stale"), lag


def classify_vix(value):
    value = finite(value)
    if value is None:
        return "unknown", "待获取", "neutral"
    if value < 15:
        return "calm", "低波动", "positive"
    if value < 20:
        return "normal", "正常", "neutral"
    if value < 25:
        return "elevated", "偏高", "warning"
    if value < 30:
        return "high", "高风险", "warning"
    return "extreme", "极端风险", "danger"


def classify_margin(change_5d, score):
    change_5d, score = finite(change_5d), finite(score)
    if change_5d is None or score is None:
        return "building", "基线建立中", "neutral"
    if change_5d >= 1.5 and score >= 0.8:
        return "heating", "杠杆升温", "warning"
    if change_5d <= -1.0 and score <= -0.5:
        return "cooling", "杠杆降温", "positive"
    return "stable", "中性", "neutral"


def dataframe_rows(frame, date_candidates, value_candidates):
    """Normalize an OpenBB dataframe without binding to one extension version."""
    if hasattr(frame, "reset_index"):
        frame = frame.reset_index()
    columns = {str(column).lower(): column for column in getattr(frame, "columns", [])}
    date_column = next((columns[name] for name in date_candidates if name in columns), None)
    value_column = next((columns[name] for name in value_candidates if name in columns), None)
    if date_column is None or value_column is None:
        raise ValueError("OpenBB result does not contain date/close columns")
    rows = []
    for _, row in frame.iterrows():
        value = finite(row[value_column])
        if value is None:
            continue
        observed = str(row[date_column])[:10]
        rows.append({"date": observed, "value": value})
    return sorted(rows, key=lambda item: item["date"])


def fetch_vix_openbb(today=None):
    """Use the OpenBB YFinance provider, then the official CBOE CSV fallback."""
    today = today or datetime.now(BEIJING).date()
    start = today - timedelta(days=LOOKBACK_DAYS)
    errors = []
    try:
        from openbb_yfinance.models.index_historical import YFinanceIndexHistoricalFetcher

        result = asyncio.run(YFinanceIndexHistoricalFetcher.fetch_data({
            "symbol": "VIX",
            "start_date": start,
            "end_date": today,
            "interval": "1d",
        }))
        rows = []
        for item in result:
            values = item.model_dump() if hasattr(item, "model_dump") else dict(item)
            observed = str(values.get("date", ""))[:10]
            close = finite(values.get("close"))
            if observed and close is not None:
                rows.append({"date": observed, "value": close})
        rows.sort(key=lambda item: item["date"])
        if len(rows) < 2:
            raise ValueError("fewer than two VIX observations")
        return rows, "openbb-yfinance"
    except Exception as exc:
        errors.append(f"openbb-yfinance: {exc}")

    try:
        request = urllib.request.Request(
            "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv",
            headers={"User-Agent": "investment-news/1.0"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            text = response.read().decode("utf-8-sig")
        rows = []
        for item in csv.DictReader(io.StringIO(text)):
            observed = str(item.get("DATE", ""))
            try:
                observed = datetime.strptime(observed, "%m/%d/%Y").date().isoformat()
            except ValueError:
                observed = observed[:10]
            close = finite(item.get("CLOSE"))
            if observed >= start.isoformat() and close is not None:
                rows.append({"date": observed, "value": close})
        rows.sort(key=lambda item: item["date"])
        if len(rows) < 2:
            raise ValueError("fewer than two VIX observations")
        return rows, "cboe-direct"
    except Exception as exc:
        errors.append(f"cboe-direct: {exc}")
    raise RuntimeError("; ".join(errors))


def make_vix_metric(rows, provider, today=None):
    rows = rows[-MIN_OBSERVATIONS:]
    values = [row["value"] for row in rows]
    latest = rows[-1]
    status, lag = freshness(latest["date"], 3, today=today)
    level, label, tone = classify_vix(latest["value"])
    return {
        "id": "vix",
        "label": "VIX海外风险",
        "value": round(latest["value"], 2),
        "unit": "点",
        "as_of": latest["date"],
        "lag_days": lag,
        "status": status,
        "confidence": "high" if provider == "cboe-direct" else "medium",
        "source": "CBOE" if provider == "cboe-direct" else "OpenBB/YFinance",
        "source_url": "https://www.cboe.com/tradable_products/vix/vix_historical_data/",
        "change_1d_pct": pct_change(values[-1], values[-2]) if len(values) >= 2 else None,
        "percentile_20d": percentile_rank(values, values[-1]),
        "level": level,
        "state_label": label,
        "tone": tone,
        "sample_size": len(values),
    }


def clean_date(value):
    digits = "".join(character for character in str(value) if character.isdigit())
    return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}" if len(digits) >= 8 else ""


def fetch_margin_akshare(today=None):
    import akshare as ak

    today = today or datetime.now(BEIJING).date()
    start = (today - timedelta(days=LOOKBACK_DAYS)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")
    sh = ak.stock_margin_sse(start_date=start, end_date=end)
    if sh is None or sh.empty:
        raise RuntimeError("SSE margin result is empty")
    sh_rows = []
    for _, row in sh.iterrows():
        observed = clean_date(row.get("信用交易日期"))
        financing = finite(row.get("融资余额"))
        total = finite(row.get("融资融券余额"))
        buy = finite(row.get("融资买入额"))
        if observed and financing is not None and total is not None:
            sh_rows.append({
                "date": observed,
                "financing": financing / 1e8,
                "total": total / 1e8,
                "buy": (buy or 0) / 1e8,
            })
    sh_rows.sort(key=lambda item: item["date"], reverse=True)
    errors = []
    for sh_row in sh_rows[:7]:
        try:
            sz = ak.stock_margin_szse(date=sh_row["date"].replace("-", ""))
            if sz is None or sz.empty:
                raise ValueError("empty result")
            row = sz.iloc[0]
            financing = finite(row.get("融资余额"))
            total = finite(row.get("融资融券余额"))
            buy = finite(row.get("融资买入额"))
            if financing is None or total is None:
                raise ValueError("missing balance fields")
            combined = {
                "date": sh_row["date"],
                "financing": sh_row["financing"] + financing,
                "total": sh_row["total"] + total,
                "buy": sh_row["buy"] + (buy or 0),
            }
            return [combined]
        except Exception as exc:
            errors.append(f"{sh_row['date']}: {exc}")
    raise RuntimeError("SZSE margin snapshot unavailable: " + "; ".join(errors[:3]))


def make_margin_metric(rows, today=None):
    rows = rows[-MIN_OBSERVATIONS:]
    latest = rows[-1]
    values = [row["financing"] for row in rows]
    change_5d = pct_change(values[-1], values[-6]) if len(values) >= 6 else None
    score = zscore(values, values[-1]) if len(values) >= MIN_OBSERVATIONS else None
    status, lag = freshness(latest["date"], 4, today=today)
    level, label, tone = classify_margin(change_5d, score)
    return {
        "id": "margin_balance",
        "label": "A股杠杆情绪",
        "value": round(latest["financing"], 2),
        "total_margin_balance": round(latest["total"], 2),
        "financing_buy_amount": round(latest["buy"], 2),
        "unit": "亿元",
        "as_of": latest["date"],
        "lag_days": lag,
        "status": status,
        "confidence": "high",
        "source": "SSE+SZSE via AKShare",
        "source_url": "https://www.sse.com.cn/market/othersdata/margin/sum/",
        "change_1d_pct": pct_change(values[-1], values[-2]) if len(values) >= 2 else None,
        "change_5d_pct": change_5d,
        "zscore_20d": score,
        "level": level,
        "state_label": label,
        "tone": tone,
        "sample_size": len(values),
    }


def unavailable_metric(metric_id, label, error):
    return {
        "id": metric_id,
        "label": label,
        "value": None,
        "unit": "点" if metric_id == "vix" else "亿元",
        "as_of": None,
        "lag_days": None,
        "status": "unavailable",
        "confidence": "low",
        "source": "OpenBB" if metric_id == "vix" else "SSE+SZSE via AKShare",
        "state_label": "待获取",
        "level": "unknown",
        "tone": "neutral",
        "error": str(error)[:240],
    }


def preserve_or_unavailable(previous, metric_id, label, error, today=None):
    old = next((item for item in previous.get("metrics", []) if item.get("id") == metric_id), None)
    if not old or old.get("value") is None:
        return unavailable_metric(metric_id, label, error)
    kept = dict(old)
    kept["status"] = "stale"
    kept["lag_days"] = age_days(kept.get("as_of"), today=today)
    kept["error"] = str(error)[:240]
    return kept


def state_from_metric(metric, title, summary):
    return {
        "title": title,
        "level": metric.get("level", "unknown"),
        "label": metric.get("state_label", "待获取"),
        "tone": metric.get("tone", "neutral"),
        "status": metric.get("status", "unavailable"),
        "summary": summary,
        "metric_id": metric["id"],
    }


def build_payload(previous=None, now=None, vix_fetcher=fetch_vix_openbb, margin_fetcher=fetch_margin_akshare):
    previous = previous or {}
    now = now or datetime.now(BEIJING)
    today = now.date()
    warnings = []
    try:
        vix_rows, provider = vix_fetcher(today=today)
        vix = make_vix_metric(vix_rows, provider, today=today)
    except Exception as exc:
        warnings.append(f"VIX refresh failed: {exc}")
        vix = preserve_or_unavailable(previous, "vix", "VIX海外风险", exc, today=today)
    try:
        margin_snapshot = margin_fetcher(today=today)
        old_rows = previous.get("history", {}).get("margin_balance", [])
        by_date = {
            row.get("date"): row
            for row in [*old_rows, *margin_snapshot]
            if row.get("date")
        }
        margin_rows = sorted(by_date.values(), key=lambda row: row["date"])[-30:]
        margin = make_margin_metric(margin_rows, today=today)
    except Exception as exc:
        warnings.append(f"Margin refresh failed: {exc}")
        margin_rows = previous.get("history", {}).get("margin_balance", [])
        margin = preserve_or_unavailable(previous, "margin_balance", "A股杠杆情绪", exc, today=today)

    vix_summary = "用于校准海外风险环境，不直接触发A股买卖。"
    margin_summary = "观察融资余额5日变化与20日位置，资金流不在本阶段计分。"
    return {
        "version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "states": {
            "overseas_risk": state_from_metric(vix, "海外风险", vix_summary),
            "leverage_sentiment": state_from_metric(margin, "杠杆情绪", margin_summary),
        },
        "metrics": [vix, margin],
        "history": {"margin_balance": margin_rows},
        "warnings": warnings,
        "methodology": {
            "vix": "优先使用OpenBB/YFinance标准化接口，限流或失败时切换CBOE官方历史数据；显示最新值、单日变化和20日分位。",
            "margin_balance": "AKShare封装上交所与深交所官方汇总；合并融资余额，显示1日/5日变化和20日Z-score。",
            "boundary": "两项指标分别描述海外风险与A股杠杆情绪，暂不合成总分，也不生成无条件交易指令。",
        },
    }


def load_previous(path=OUTPUT):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def write_payload(payload, path=OUTPUT):
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, path)


def main():
    payload = build_payload(previous=load_previous())
    write_payload(payload)
    for metric in payload["metrics"]:
        print(metric["id"], metric.get("value"), metric.get("status"), metric.get("as_of"))
    for warning in payload["warnings"]:
        print("warning:", warning)


if __name__ == "__main__":
    main()
