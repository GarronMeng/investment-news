#!/usr/bin/env python3
"""Append material Decision Matrix states to a monthly JSONL ledger.

One record is kept per asset/date/state tuple. Intraday score drift that does not
change the semantic state is intentionally deduplicated so forward evaluation is
not dominated by repeated workflow runs.
"""

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEIJING = timezone(timedelta(hours=8))


def load(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def close_on_or_before(series, target_date):
    rows = [row for row in series.get("rows", []) if row.get("date") and row.get("close") is not None]
    eligible = [row for row in rows if row["date"] <= target_date]
    return eligible[-1] if eligible else None


def state_identity(item):
    raw = "|".join(
        [
            str(item.get("code")),
            str(item.get("as_of")),
            str(item.get("thesis_state")),
            str(item.get("evidence_state")),
            str(item.get("matrix_direction")),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def record_for(item, matrix, history, now):
    code = str(item.get("code"))
    signal_date = item.get("as_of")
    asset_row = close_on_or_before(history.get("assets", {}).get(code, {}), signal_date) if signal_date else None
    benchmark_row = close_on_or_before(history.get("benchmark", {}), signal_date) if signal_date else None
    layers = {
        name: {
            "score": layer.get("score"),
            "available": layer.get("available"),
            "confidence": layer.get("confidence"),
        }
        for name, layer in (item.get("layers") or {}).items()
    }
    return {
        "state_id": state_identity(item),
        "created_at": now.isoformat(timespec="seconds"),
        "matrix_generated_at": matrix.get("generated_at"),
        "signal_date": signal_date,
        "asset": code,
        "name": item.get("name"),
        "group": item.get("group"),
        "base_bias": item.get("base_bias"),
        "matrix_direction": item.get("matrix_direction"),
        "thesis_state": item.get("thesis_state"),
        "evidence_state": item.get("evidence_state"),
        "composite_score": item.get("composite_score"),
        "coverage": item.get("coverage"),
        "confluence": item.get("confluence"),
        "conflict_score": item.get("conflict_score"),
        "attention_score": item.get("attention_score"),
        "entry_close": asset_row.get("close") if asset_row else None,
        "entry_benchmark_close": benchmark_row.get("close") if benchmark_row else None,
        "layers": layers,
    }


def main():
    now = datetime.now(BEIJING)
    matrix = load(os.path.join(ROOT, "decision_matrix.json"))
    history = load(os.path.join(ROOT, "market_history.json"))
    state_dir = os.path.join(ROOT, "matrix_states")
    os.makedirs(state_dir, exist_ok=True)
    path = os.path.join(state_dir, now.strftime("%Y-%m") + ".jsonl")

    existing = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                try:
                    existing.add(json.loads(line).get("state_id"))
                except ValueError:
                    continue

    appended = 0
    with open(path, "a", encoding="utf-8") as handle:
        for item in matrix.get("assets", {}).values():
            if not item.get("as_of") or item.get("evidence_state") == "insufficient":
                continue
            record = record_for(item, matrix, history, now)
            if record["state_id"] in existing:
                continue
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            existing.add(record["state_id"])
            appended += 1

    print("matrix ledger", os.path.relpath(path, ROOT), "appended", appended)


if __name__ == "__main__":
    main()
