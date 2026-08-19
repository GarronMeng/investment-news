#!/usr/bin/env python3
"""Attach leverage, southbound and CFFEX context to Daily Flash."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLASH = os.path.join(ROOT, "daily_flash.json")
SENTIMENT = os.path.join(ROOT, "sentiment.json")
EXTRAS = os.path.join(ROOT, "market_extras.json")


def load(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def margin_metric(sentiment):
    for row in sentiment.get("metrics", []):
        if row.get("id") == "margin_balance":
            return {
                "status": row.get("status"),
                "as_of": row.get("as_of"),
                "financing_balance_cny_100m": row.get("value"),
                "total_margin_balance_cny_100m": row.get("total_margin_balance"),
                "financing_buy_cny_100m": row.get("financing_buy_amount"),
                "change_1d_pct": row.get("change_1d_pct"),
                "change_5d_pct": row.get("change_5d_pct"),
                "zscore_20d": row.get("zscore_20d"),
                "source": row.get("source"),
            }
    return {"status": "unavailable", "as_of": None}


def append_conclusion(base, margin, southbound, futures):
    bits = []
    if margin.get("financing_balance_cny_100m") is not None:
        change = margin.get("change_5d_pct")
        text = f"融资余额{margin['financing_balance_cny_100m']:.0f}亿元"
        if change is not None:
            text += f"，5日{change:+.2f}%"
        if margin.get("status") != "fresh":
            text += f"（{margin.get('status')}）"
        bits.append(text)
    if southbound.get("net_buy_cny_100m") is not None:
        text = f"南向成交净买额{southbound['net_buy_cny_100m']:+.1f}亿元"
        if southbound.get("status") != "fresh":
            text += f"（{southbound.get('status')}）"
        bits.append(text)
    basis_rows = [row for row in futures if row.get("basis_pct") is not None and row.get("status") == "fresh"]
    if basis_rows:
        strongest = max(basis_rows, key=lambda row: abs(float(row["basis_pct"])))
        bits.append(f"{strongest.get('underlying')}股指期货基差{float(strongest['basis_pct']):+.2f}%")
    return base + ("资金/期指：" + "；".join(bits) + "。" if bits else "")


def augment(flash, sentiment, extras):
    market = flash.setdefault("market", {})
    margin = margin_metric(sentiment)
    southbound = extras.get("southbound") or {"status": "unavailable"}
    futures = extras.get("index_futures") or []
    market["funding_and_futures"] = {
        "margin": margin,
        "southbound": southbound,
        "index_futures": futures,
    }
    flash["core_conclusion"] = append_conclusion(flash.get("core_conclusion", ""), margin, southbound, futures)
    flash.setdefault("sources", {})["sentiment"] = sentiment.get("generated_at")
    flash["sources"]["market_extras"] = extras.get("generated_at")
    return flash


def main():
    payload = augment(load(FLASH), load(SENTIMENT), load(EXTRAS))
    tmp = FLASH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(tmp, FLASH)
    print("augmented Daily Flash funding/futures")


if __name__ == "__main__":
    main()
