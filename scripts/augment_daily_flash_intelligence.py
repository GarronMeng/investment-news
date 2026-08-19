#!/usr/bin/env python3
"""Attach macro/global catalysts and theme earnings breadth to Daily Flash."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLASH = os.path.join(ROOT, "daily_flash.json")
MACRO = os.path.join(ROOT, "macro_calendar.json")
THEME = os.path.join(ROOT, "theme_earnings.json")


def load(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def next_catalysts(macro, limit=2):
    rows = sorted(
        macro.get("events", []),
        key=lambda row: (row.get("date") or "9999-12-31", row.get("time") or "99:99", -(row.get("importance") or 0)),
    )
    preferred = [row for row in rows if (row.get("importance") or 0) >= 3]
    chosen = preferred[:limit] if preferred else rows[:limit]
    return chosen


def enrich_conclusion(flash, macro, theme):
    base = str(flash.get("core_conclusion") or "").strip()
    additions = []
    upcoming = next_catalysts(macro)
    if upcoming:
        labels = []
        for row in upcoming:
            when = (row.get("date") or "")[5:10]
            if row.get("time"):
                when += " " + str(row["time"])
            labels.append(f"{when} {row.get('title','')}")
        additions.append("下一催化：" + "；".join(labels))
    summary = theme.get("summary") or {}
    if summary.get("companies") is not None:
        additions.append(
            f"主线财报已确认披露 {int(summary.get('reported') or 0)}/{int(summary.get('companies') or 0)} 个研究样本"
        )
    if additions:
        suffix = "。".join(additions) + "。"
        if suffix not in base:
            base = (base + (" " if base else "") + suffix).strip()
    flash["core_conclusion"] = base


def main():
    flash = load(FLASH)
    macro = load(MACRO)
    theme = load(THEME)
    flash["macro_calendar"] = macro.get("events", [])
    flash["macro_calendar_summary"] = macro.get("summary", {})
    flash["theme_earnings"] = theme.get("themes", [])
    flash["theme_earnings_summary"] = theme.get("summary", {})
    flash["theme_earnings_period"] = theme.get("report_period")
    enrich_conclusion(flash, macro, theme)
    sources = flash.setdefault("sources", {})
    sources["macro_calendar"] = macro.get("generated_at")
    sources["theme_earnings"] = theme.get("generated_at")
    quality = flash.setdefault("quality", {})
    quality["macro_calendar"] = {
        "events": len(macro.get("events", [])),
        "warnings": len(macro.get("warnings", [])),
        "horizon_days": macro.get("horizon_days"),
    }
    quality["theme_earnings"] = {
        "status": theme.get("status"),
        "reported": (theme.get("summary") or {}).get("reported"),
        "companies": (theme.get("summary") or {}).get("companies"),
    }
    temporary = FLASH + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(flash, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, FLASH)
    print("attached macro calendar", len(flash["macro_calendar"]), "theme earnings", len(flash["theme_earnings"]))


if __name__ == "__main__":
    main()
