#!/usr/bin/env python3
"""Evaluate Decision Matrix state labels on future trading observations.

Directional states are judged against benchmark excess return in the matrix
direction. Neutral/conflict states are not assigned a fake hit rate; their
future absolute excess dispersion is still measured for later comparison.
"""

import glob
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "matrix_evaluation.json")
BEIJING = timezone(timedelta(hours=8))
HORIZONS = (1, 5, 20)
MIN_SAMPLE_FOR_READOUT = 8


def load(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def ledger_records():
    output = []
    for path in sorted(glob.glob(os.path.join(ROOT, "matrix_states", "*.jsonl"))):
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


def benchmark_close(rows, target_date):
    matches = [row for row in rows if row.get("date") == target_date and row.get("close") is not None]
    return float(matches[-1]["close"]) if matches else None


def mean(values):
    values = [float(v) for v in values if v is not None]
    return sum(values) / len(values) if values else None


def rounded(value, digits=6):
    return round(float(value), digits) if value is not None else None


def settle_record(record, history):
    rows = history.get("assets", {}).get(str(record.get("asset")), {}).get("rows", [])
    benchmark_rows = history.get("benchmark", {}).get("rows", [])
    entry_idx = index_at_or_after(rows, record.get("signal_date", ""))
    if entry_idx is None:
        return {"state_id": record.get("state_id"), "status": "unavailable"}

    entry = rows[entry_idx]
    entry_close = float(entry["close"])
    entry_benchmark = benchmark_close(benchmark_rows, entry["date"])
    direction = record.get("matrix_direction")
    horizons = {}
    for periods in HORIZONS:
        target_idx = entry_idx + periods
        key = f"t{periods}"
        if target_idx >= len(rows):
            horizons[key] = {"status": "pending"}
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
        if direction == "bullish":
            directional_excess = judged
        elif direction == "bearish":
            directional_excess = -judged
        else:
            directional_excess = None
        horizons[key] = {
            "status": "settled",
            "date": target["date"],
            "asset_return": rounded(asset_return),
            "benchmark_return": rounded(benchmark_return),
            "excess_return": rounded(excess),
            "absolute_excess": rounded(abs(excess)) if excess is not None else None,
            "directional_excess": rounded(directional_excess),
            "correct": directional_excess > 0 if directional_excess is not None else None,
        }

    return {
        "state_id": record.get("state_id"),
        "asset": record.get("asset"),
        "name": record.get("name"),
        "signal_date": record.get("signal_date"),
        "matrix_direction": direction,
        "thesis_state": record.get("thesis_state"),
        "evidence_state": record.get("evidence_state"),
        "composite_score": record.get("composite_score"),
        "confluence": record.get("confluence"),
        "conflict_score": record.get("conflict_score"),
        "entry_date": entry["date"],
        "entry_close": entry_close,
        "horizons": horizons,
    }


def aggregate(rows, group_field):
    grouped = defaultdict(list)
    for row in rows:
        key = row.get(group_field) or "unknown"
        grouped[key].append(row)

    output = {}
    for key, records in sorted(grouped.items()):
        horizons = {}
        for periods in HORIZONS:
            hkey = f"t{periods}"
            settled = [r["horizons"][hkey] for r in records if r.get("horizons", {}).get(hkey, {}).get("status") == "settled"]
            directional = [x for x in settled if x.get("directional_excess") is not None]
            wins = sum(x.get("correct") is True for x in directional)
            horizons[hkey] = {
                "settled": len(settled),
                "directional_settled": len(directional),
                "win_rate": rounded(wins / len(directional), 4) if directional else None,
                "mean_directional_excess": rounded(mean([x.get("directional_excess") for x in directional])),
                "mean_excess_return": rounded(mean([x.get("excess_return") for x in settled])),
                "mean_absolute_excess": rounded(mean([x.get("absolute_excess") for x in settled])),
                "readout": "usable" if len(directional) >= MIN_SAMPLE_FOR_READOUT else "insufficient_sample",
            }
        output[key] = {"records": len(records), "horizons": horizons}
    return output


def main():
    history = load(os.path.join(ROOT, "market_history.json"))
    records = ledger_records()
    evaluations = [settle_record(record, history) for record in records]
    usable = [row for row in evaluations if row.get("status") != "unavailable"]

    payload = {
        "version": 1,
        "generated_at": datetime.now(BEIJING).isoformat(timespec="seconds"),
        "history_generated_at": history.get("generated_at"),
        "records": len(records),
        "evaluations": evaluations,
        "by_thesis_state": aggregate(usable, "thesis_state"),
        "by_evidence_state": aggregate(usable, "evidence_state"),
        "methodology": {
            "directional": "bullish/bearish matrix_direction uses future benchmark excess return; bearish signs are inverted so positive directional_excess means the matrix direction was correct.",
            "neutral": "neutral/conflict states receive no synthetic win rate; future absolute excess dispersion is measured instead.",
            "deduplication": "matrix ledger records one asset/date/semantic-state tuple, avoiding repeated intraday workflow runs as duplicate samples.",
            "minimum_readout": f"win-rate readout remains insufficient_sample until at least {MIN_SAMPLE_FOR_READOUT} directional settled observations exist in a group.",
        },
        "boundary": "Historical validation only; these statistics are not converted into future probabilities or automatic trading actions.",
    }
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("matrix evaluations", len(evaluations), "records", len(records))


if __name__ == "__main__":
    main()
