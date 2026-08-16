#!/usr/bin/env python3
"""Append material public-research decisions to a monthly JSONL ledger."""

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


def main():
    now = datetime.now(BEIJING)
    decisions = load(os.path.join(ROOT, "decisions.json"))
    history = load(os.path.join(ROOT, "market_history.json"))
    signal_dir = os.path.join(ROOT, "signals")
    os.makedirs(signal_dir, exist_ok=True)
    path = os.path.join(signal_dir, now.strftime("%Y-%m") + ".jsonl")

    existing = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                try:
                    existing.add(json.loads(line).get("decision_id"))
                except ValueError:
                    continue

    appended = 0
    with open(path, "a", encoding="utf-8") as handle:
        for decision in decisions.get("decisions", []):
            if decision.get("status") not in {"active", "watch", "market_watch"}:
                continue
            signal_date = decision.get("as_of")
            if not signal_date:
                continue
            identity = "|".join(
                [
                    str(decision.get("asset")), signal_date,
                    str(decision.get("bias")), str(decision.get("status")),
                    str(decision.get("event_score")), str(decision.get("market_score")),
                    str(decision.get("conviction")), str(decisions.get("source", {}).get("data_generated_at")),
                ]
            )
            decision_id = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:16]
            if decision_id in existing:
                continue

            asset_series = history.get("assets", {}).get(str(decision.get("asset")), {})
            asset_row = close_on_or_before(asset_series, signal_date)
            benchmark_row = close_on_or_before(history.get("benchmark", {}), signal_date)
            record = {
                "decision_id": decision_id,
                "created_at": now.isoformat(timespec="seconds"),
                "signal_date": signal_date,
                "asset": decision.get("asset"),
                "name": decision.get("name"),
                "bias": decision.get("bias"),
                "status": decision.get("status"),
                "conviction": decision.get("conviction"),
                "event_score": decision.get("event_score"),
                "market_score": decision.get("market_score"),
                "evidence_mode": decision.get("evidence_mode"),
                "trend_state": decision.get("trend_state"),
                "entry_close": asset_row.get("close") if asset_row else None,
                "entry_benchmark_close": benchmark_row.get("close") if benchmark_row else None,
                "confirmation": decision.get("confirmation", []),
                "invalidation": decision.get("invalidation", []),
                "expires_at": decision.get("expires_at"),
                "source": decisions.get("source", {}),
            }
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            existing.add(decision_id)
            appended += 1

    print("ledger", os.path.relpath(path, ROOT), "appended", appended)


if __name__ == "__main__":
    main()
