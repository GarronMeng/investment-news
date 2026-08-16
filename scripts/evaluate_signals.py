#!/usr/bin/env python3
"""Evaluate logged research signals on future trading observations."""

import glob
import json
import os
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "signal_evaluation.json")
BEIJING = timezone(timedelta(hours=8))
HORIZONS = (1, 5, 20)


def load(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def ledger_records():
    output = []
    for path in sorted(glob.glob(os.path.join(ROOT, "signals", "*.jsonl"))):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                try:
                    output.append(json.loads(line))
                except ValueError:
                    continue
    return output


def index_at_or_after(rows, target):
    for idx, row in enumerate(rows):
        if row.get("date") and row["date"] >= target and row.get("close") is not None:
            return idx
    return None


def benchmark_close(benchmark_rows, target_date):
    matches = [row for row in benchmark_rows if row.get("date") == target_date and row.get("close") is not None]
    return float(matches[-1]["close"]) if matches else None


def directional_stats(record, rows, entry_idx):
    entry = float(rows[entry_idx]["close"])
    window = rows[entry_idx : min(len(rows), entry_idx + 21)]
    highs = [float(row.get("high", row["close"])) for row in window if row.get("high", row.get("close")) is not None]
    lows = [float(row.get("low", row["close"])) for row in window if row.get("low", row.get("close")) is not None]
    max_up = max((value / entry - 1 for value in highs), default=None)
    max_down = min((value / entry - 1 for value in lows), default=None)
    if record.get("bias") == "bearish":
        mfe = -max_down if max_down is not None else None
        mae = -max_up if max_up is not None else None
    else:
        mfe = max_up
        mae = max_down
    return mfe, mae


def main():
    history = load(os.path.join(ROOT, "market_history.json"))
    benchmark_rows = history.get("benchmark", {}).get("rows", [])
    evaluations = []

    for record in ledger_records():
        rows = history.get("assets", {}).get(str(record.get("asset")), {}).get("rows", [])
        entry_idx = index_at_or_after(rows, record.get("signal_date", ""))
        if entry_idx is None:
            evaluations.append({"decision_id": record.get("decision_id"), "status": "unavailable"})
            continue

        entry_row = rows[entry_idx]
        entry_close = float(entry_row["close"])
        entry_benchmark = benchmark_close(benchmark_rows, entry_row["date"])
        horizons = {}
        for periods in HORIZONS:
            target_idx = entry_idx + periods
            if target_idx >= len(rows):
                horizons[f"t{periods}"] = {"status": "pending"}
                continue
            target = rows[target_idx]
            asset_return = float(target["close"]) / entry_close - 1
            target_benchmark = benchmark_close(benchmark_rows, target["date"])
            benchmark_return = (
                target_benchmark / entry_benchmark - 1
                if target_benchmark is not None and entry_benchmark not in (None, 0)
                else None
            )
            excess = asset_return - benchmark_return if benchmark_return is not None else None
            judged = excess if excess is not None else asset_return
            bias = record.get("bias")
            correct = judged > 0 if bias == "bullish" else judged < 0 if bias == "bearish" else None
            horizons[f"t{periods}"] = {
                "status": "settled",
                "date": target["date"],
                "asset_return": round(asset_return, 6),
                "benchmark_return": round(benchmark_return, 6) if benchmark_return is not None else None,
                "excess_return": round(excess, 6) if excess is not None else None,
                "correct": correct,
            }

        mfe, mae = directional_stats(record, rows, entry_idx)
        evaluations.append(
            {
                "decision_id": record.get("decision_id"),
                "asset": record.get("asset"),
                "name": record.get("name"),
                "signal_date": record.get("signal_date"),
                "bias": record.get("bias"),
                "research_status": record.get("status"),
                "conviction": record.get("conviction"),
                "entry_date": entry_row["date"],
                "entry_close": entry_close,
                "mfe_20d": round(mfe, 6) if mfe is not None else None,
                "mae_20d": round(mae, 6) if mae is not None else None,
                "horizons": horizons,
            }
        )

    summary = {}
    for periods in HORIZONS:
        key = f"t{periods}"
        settled = [row["horizons"][key] for row in evaluations if row.get("horizons", {}).get(key, {}).get("status") == "settled" and row["horizons"][key].get("correct") is not None]
        wins = sum(item["correct"] is True for item in settled)
        excess_values = [item["excess_return"] for item in settled if item.get("excess_return") is not None]
        summary[key] = {
            "settled": len(settled),
            "win_rate": round(wins / len(settled), 4) if settled else None,
            "mean_excess_return": round(sum(excess_values) / len(excess_values), 6) if excess_values else None,
        }

    payload = {
        "version": 1,
        "generated_at": datetime.now(BEIJING).isoformat(timespec="seconds"),
        "history_generated_at": history.get("generated_at"),
        "summary": summary,
        "evaluations": evaluations,
        "methodology": "Forward evaluation uses future trading observations; correctness is based on benchmark excess return when benchmark data is available, otherwise raw return. MFE/MAE are directional over up to 20 future observations.",
    }
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("evaluations", len(evaluations), summary)


if __name__ == "__main__":
    main()
