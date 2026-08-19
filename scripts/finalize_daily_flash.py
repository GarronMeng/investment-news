#!/usr/bin/env python3
"""Finalize Daily Flash display metrics after the presentation build.

This pass prevents unavailable Matrix layers from appearing as neutral zeroes in
theme cards. It also records an integrity block consumed by the dashboard and CI.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLASH = os.path.join(ROOT, "daily_flash.json")
MATRIX = os.path.join(ROOT, "decision_matrix.json")

THEMES = {
    "存储": ["603986", "001309"],
    "AI光通信 / CPO": ["300308"],
    "PCB / 消费电子": ["002384"],
    "半导体工程 / 封测": ["600667"],
    "被动元件": ["000636"],
    "创新药": ["517380"],
    "黄金": ["518880"],
    "白银": ["161226"],
}


def load(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def mean_layer(items, layer_name):
    values = []
    for item in items:
        layer = (item.get("layers") or {}).get(layer_name) or {}
        if not layer.get("available"):
            continue
        value = layer.get("score")
        if isinstance(value, (int, float)):
            values.append(float(value))
    return round(sum(values) / len(values), 1) if values else None


def finalize(flash, matrix):
    assets = matrix.get("assets") or {}
    theme_map = {row.get("theme"): row for row in flash.get("themes", [])}
    failures = []
    for theme, codes in THEMES.items():
        row = theme_map.get(theme)
        if not row:
            continue
        items = [assets[code] for code in codes if code in assets]
        row["technical_score"] = mean_layer(items, "technical")
        row["industry_score"] = mean_layer(items, "industry")
        row["event_score"] = mean_layer(items, "event")
        if row["industry_score"] == 0:
            eligible = [((item.get("layers") or {}).get("industry") or {}).get("available") for item in items]
            if eligible and not any(eligible):
                failures.append({"theme": theme, "field": "industry_score", "reason": "unavailable layer rendered as zero"})
    flash["integrity"] = {
        "status": "ok" if not failures else "failed",
        "checked_themes": len(theme_map),
        "failures": failures,
        "rule": "theme layer metrics average only final eligible Matrix layers; unavailable is null, never zero",
    }
    return flash


def main():
    payload = finalize(load(FLASH), load(MATRIX))
    if payload.get("integrity", {}).get("status") != "ok":
        raise RuntimeError(payload["integrity"])
    tmp = FLASH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(tmp, FLASH)
    print("finalized Daily Flash", payload.get("integrity"))


if __name__ == "__main__":
    main()
