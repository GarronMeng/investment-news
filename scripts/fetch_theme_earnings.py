#!/usr/bin/env python3
"""Track earnings breadth for representative A-share companies by investment theme.

The tracker fetches Eastmoney earnings and appointment tables, then filters a
public research universe. Financial fields are exposed only when the announcement
is not future-dated. Same-day rows require a corroborating public financial-report
notice, preventing preloaded tables from leaking results before publication.
Undisclosed results remain pending/scheduled rather than being inferred.
"""

from __future__ import annotations

import json
import math
import os
from datetime import date, datetime, timedelta, timezone
from statistics import median

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "theme_earnings.json")
UNIVERSE = os.path.join(ROOT, "theme_earnings_universe.json")
BEIJING = timezone(timedelta(hours=8))


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


def normalize_date(value):
    text = str(value or "").strip()[:10].replace("/", "-")
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        return None


def report_period(today):
    year = today.year
    if today.month <= 3:
        return f"{year-1}1231", f"{year-1}年报"
    if today.month <= 5:
        return f"{year}0331", f"{year}一季报"
    if today.month <= 9:
        return f"{year}0630", f"{year}半年报"
    if today.month <= 11:
        return f"{year}0930", f"{year}三季报"
    return f"{year}1231", f"{year}年报"


def latest_appointment(row):
    for key in ("三次变更日期", "二次变更日期", "一次变更日期", "首次预约时间", "首次预约"):
        value = normalize_date(row.get(key))
        if value:
            return value
    return None


def frame_by_code(frame, code_keys=("股票代码", "代码")):
    output = {}
    if frame is None or getattr(frame, "empty", True):
        return output
    for _, series in frame.iterrows():
        row = series.to_dict()
        raw = None
        for key in code_keys:
            if row.get(key) is not None:
                raw = row.get(key)
                break
        code = str(raw or "").strip().zfill(6)
        if code:
            output[code] = row
    return output


def notice_codes(frame):
    codes = set()
    if frame is None or getattr(frame, "empty", True):
        return codes
    for _, series in frame.iterrows():
        row = series.to_dict()
        code = str(row.get("代码") or row.get("股票代码") or "").strip().zfill(6)
        title = str(row.get("公告标题") or "")
        notice_type = str(row.get("公告类型") or "")
        if code and any(key in (title + notice_type) for key in ("半年度报告", "年度报告", "季度报告", "财务报告", "业绩报告")):
            codes.add(code)
    return codes


def filter_same_day_earnings(frame, today, confirmed_codes):
    if frame is None or getattr(frame, "empty", True):
        return frame, 0
    keep = []
    withheld = 0
    for idx, series in frame.iterrows():
        row = series.to_dict()
        announcement = normalize_date(row.get("最新公告日期"))
        code = str(row.get("股票代码") or row.get("代码") or "").strip().zfill(6)
        if announcement == today.isoformat() and code not in confirmed_codes:
            withheld += 1
            continue
        keep.append(idx)
    return frame.loc[keep].copy(), withheld


def fetch_tables(today=None):
    import akshare as ak

    today = today or datetime.now(BEIJING).date()
    period_code, period_label = report_period(today)
    warnings = []
    earnings = None
    appointments = None
    try:
        earnings = ak.stock_yjbb_em(date=period_code)
    except Exception as exc:
        warnings.append(f"stock_yjbb_em {period_code}: {exc}")
    try:
        appointments = ak.stock_yysj_em(symbol="沪深A股", date=period_code)
    except Exception as exc:
        warnings.append(f"stock_yysj_em {period_code}: {exc}")
    if earnings is not None and not getattr(earnings, "empty", True):
        confirmed = set()
        try:
            notices = ak.stock_notice_report(symbol="财务报告", date=today.strftime("%Y%m%d"))
            confirmed = notice_codes(notices)
        except Exception as exc:
            warnings.append(f"stock_notice_report {today:%Y%m%d}: {exc}; same-day financial rows withheld")
        earnings, withheld = filter_same_day_earnings(earnings, today, confirmed)
        if withheld:
            warnings.append(f"withheld {withheld} same-day earnings rows without corroborating public financial-report notice")
    return earnings, appointments, warnings, period_code, period_label


def earnings_signal(revenue_yoy, profit_yoy):
    if revenue_yoy is None or profit_yoy is None:
        return "unknown"
    if revenue_yoy >= 20 and profit_yoy >= 20:
        return "strong_growth"
    if revenue_yoy > 0 and profit_yoy > 0:
        return "positive_growth"
    if revenue_yoy <= 0 and profit_yoy <= 0:
        return "weak_growth"
    return "mixed"


def pending_report(code, configured_name, appointment, source="东方财富 via AKShare", reason=None):
    return {
        "code": code,
        "name": configured_name,
        "status": "scheduled" if appointment else "pending",
        "announcement_date": None,
        "scheduled_date": appointment,
        "revenue": None,
        "revenue_yoy_pct": None,
        "net_profit": None,
        "net_profit_yoy_pct": None,
        "gross_margin_pct": None,
        "earnings_signal": "not_reported",
        "industry": None,
        "source": source if appointment else "awaiting public report",
        "reason": reason,
    }


def normalize_report(code, configured_name, row, appointment, today=None):
    today = today or datetime.now(BEIJING).date()
    if not row:
        return pending_report(code, configured_name, appointment)
    announcement = normalize_date(row.get("最新公告日期"))
    if not announcement:
        return pending_report(code, configured_name, appointment, reason="report row present but announcement date missing; financial fields withheld")
    if date.fromisoformat(announcement) > today:
        return pending_report(code, configured_name, appointment or announcement, reason="future-dated report row withheld to prevent look-ahead")
    revenue = finite(row.get("营业总收入-营业总收入"))
    revenue_yoy = finite(row.get("营业总收入-同比增长"))
    profit = finite(row.get("净利润-净利润"))
    profit_yoy = finite(row.get("净利润-同比增长"))
    gross_margin = finite(row.get("销售毛利率"))
    return {
        "code": code,
        "name": str(row.get("股票简称") or configured_name),
        "status": "reported",
        "announcement_date": announcement,
        "scheduled_date": appointment,
        "revenue": revenue,
        "revenue_yoy_pct": revenue_yoy,
        "net_profit": profit,
        "net_profit_yoy_pct": profit_yoy,
        "gross_margin_pct": gross_margin,
        "earnings_signal": earnings_signal(revenue_yoy, profit_yoy),
        "industry": row.get("所处行业"),
        "source": "东方财富 via AKShare + 公告确认",
        "reason": None,
    }


def theme_summary(companies):
    reported = [item for item in companies if item.get("status") == "reported"]
    revenue_growth = [item["revenue_yoy_pct"] for item in reported if item.get("revenue_yoy_pct") is not None]
    profit_growth = [item["net_profit_yoy_pct"] for item in reported if item.get("net_profit_yoy_pct") is not None]
    strong = sum(item.get("earnings_signal") in {"strong_growth", "positive_growth"} for item in reported)
    weak = sum(item.get("earnings_signal") == "weak_growth" for item in reported)
    if not reported:
        breadth = "awaiting_reports"
    elif strong > weak and strong >= max(1, len(reported) / 2):
        breadth = "positive"
    elif weak > strong and weak >= max(1, len(reported) / 2):
        breadth = "weak"
    else:
        breadth = "mixed"
    return {
        "total": len(companies),
        "reported": len(reported),
        "scheduled": sum(item.get("status") == "scheduled" for item in companies),
        "pending": sum(item.get("status") == "pending" for item in companies),
        "positive_reports": strong,
        "weak_reports": weak,
        "median_revenue_yoy_pct": round(median(revenue_growth), 2) if revenue_growth else None,
        "median_net_profit_yoy_pct": round(median(profit_growth), 2) if profit_growth else None,
        "breadth": breadth,
    }


def preserve_previous(previous):
    kept = dict(previous)
    kept["generated_at"] = datetime.now(BEIJING).isoformat(timespec="seconds")
    kept["status"] = "stale"
    for theme in kept.get("themes", []):
        for item in theme.get("companies", []):
            item["data_status"] = "stale"
    return kept


def build(previous=None, today=None, fetcher=fetch_tables):
    today = today or datetime.now(BEIJING).date()
    previous = previous or {}
    universe = load_json(UNIVERSE)
    try:
        earnings_frame, appointment_frame, warnings, period_code, period_label = fetcher(today=today)
    except Exception as exc:
        earnings_frame, appointment_frame, warnings = None, None, [f"theme earnings refresh: {exc}"]
        period_code, period_label = report_period(today)
    if (earnings_frame is None or getattr(earnings_frame, "empty", True)) and (appointment_frame is None or getattr(appointment_frame, "empty", True)):
        if previous.get("themes"):
            kept = preserve_previous(previous)
            kept.setdefault("warnings", []).extend(warnings)
            return kept
    earnings = frame_by_code(earnings_frame)
    appointments_raw = frame_by_code(appointment_frame)
    appointments = {code: latest_appointment(row) for code, row in appointments_raw.items()}
    themes = []
    for config in universe.get("themes", []):
        companies = []
        for company in config.get("companies", []):
            code = str(company.get("code") or "").zfill(6)
            companies.append(normalize_report(code, company.get("name") or code, earnings.get(code), appointments.get(code), today=today))
        themes.append({
            "theme": config.get("theme"),
            "summary": theme_summary(companies),
            "companies": companies,
        })
    return {
        "version": 1,
        "generated_at": datetime.now(BEIJING).isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "status": "fresh",
        "report_period_code": period_code,
        "report_period": period_label,
        "themes": themes,
        "summary": {
            "themes": len(themes),
            "companies": sum(len(theme.get("companies", [])) for theme in themes),
            "reported": sum(theme.get("summary", {}).get("reported", 0) for theme in themes),
            "scheduled": sum(theme.get("summary", {}).get("scheduled", 0) for theme in themes),
        },
        "warnings": warnings,
        "methodology": {
            "reported": "东方财富业绩报表 stock_yjbb_em via AKShare；未来公告日期不暴露财务字段；同日行必须在stock_notice_report财务报告公告中得到代码级确认。",
            "schedule": "东方财富预约披露 stock_yysj_em via AKShare；未来日期或未披露公司只显示scheduled/pending。",
            "breadth": "主题breadth只描述已确认披露样本的增长分布；样本未齐时不外推为全行业结论。",
        },
        "boundary": "主题公司池是公开研究样本，不代表推荐、持仓或收益预测；未来/未确认同日公告行不泄露财务字段。",
    }


def main():
    payload = build(previous=load_json(OUTPUT))
    temporary = OUTPUT + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, OUTPUT)
    print("theme earnings", payload.get("summary"), payload.get("report_period"), payload.get("status"))
    for warning in payload.get("warnings", []):
        print("warning:", warning)


if __name__ == "__main__":
    main()
