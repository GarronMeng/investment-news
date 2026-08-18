#!/usr/bin/env python3
"""Finalize Decision Matrix display fields after eligibility refinement.

The base matrix calculates contributors before the refinement pass. If refinement
excludes a stale or economically irrelevant layer, contributor cards must be
rebuilt from the final eligible layer set or the UI can display evidence that no
longer participates in the score.
"""

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "decision_matrix.json")
WEIGHTS = {
    "event": 25,
    "technical": 30,
    "relative_strength": 20,
    "industry": 15,
    "market_context": 10,
}


def load(path):
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


def rounded(value, digits=1):
    return round(float(value), digits) if value is not None else None


def top_contributors(layers):
    items = []
    for name, layer in (layers or {}).items():
        if name not in WEIGHTS or not layer.get("available"):
            continue
        score = finite(layer.get("score"))
        if score is None:
            continue
        impact = score * WEIGHTS[name] / 100.0
        items.append((impact, name, score, layer.get("evidence")))
    positive = sorted((x for x in items if x[0] > 0), reverse=True)[:2]
    negative = sorted((x for x in items if x[0] < 0))[:2]
    return {
        "positive": [
            {"layer": name, "score": rounded(score), "evidence": evidence}
            for _, name, score, evidence in positive
        ],
        "negative": [
            {"layer": name, "score": rounded(score), "evidence": evidence}
            for _, name, score, evidence in negative
        ],
    }


def finalize(payload):
    invalid = []
    for code, item in (payload.get("assets") or {}).items():
        item["contributors"] = top_contributors(item.get("layers"))
        unavailable = {
            name for name, layer in (item.get("layers") or {}).items()
            if not layer.get("available")
        }
        referenced = {
            row.get("layer")
            for side in ("positive", "negative")
            for row in (item.get("contributors") or {}).get(side, [])
        }
        overlap = sorted(unavailable.intersection(referenced))
        if overlap:
            invalid.append({"code": code, "layers": overlap})

    payload["integrity"] = {
        "status": "ok" if not invalid else "failed",
        "checked_assets": len(payload.get("assets") or {}),
        "excluded_layers_referenced": invalid,
        "rule": "contributors are rebuilt from final available layers after refinement",
    }
    return payload


def main():
    payload = finalize(load(OUTPUT))
    if payload.get("integrity", {}).get("status") != "ok":
        raise RuntimeError(f"matrix contributor integrity failed: {payload['integrity']}")
    temporary = OUTPUT + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, OUTPUT)
    print("finalized decision matrix", payload.get("integrity"))


if __name__ == "__main__":
    main()
