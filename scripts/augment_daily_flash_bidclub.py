#!/usr/bin/env python3
"""Attach BidClub expert intelligence to daily_flash.json without changing core scores."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLASH_PATH = os.path.join(ROOT, "daily_flash.json")
INTEL_PATH = os.path.join(ROOT, "expert_intelligence.json")


def load(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def attach(flash, intel):
    insights = intel.get("insights", []) if isinstance(intel, dict) else []
    assets = intel.get("assets", {}) if isinstance(intel, dict) else {}
    flash["expert_intelligence"] = {
        "source": "BidClub",
        "status": intel.get("status", "missing") if isinstance(intel, dict) else "missing",
        "generated_at": intel.get("generated_at") if isinstance(intel, dict) else None,
        "summary": intel.get("summary", {}) if isinstance(intel, dict) else {},
        "top_insights": insights[:8],
        "asset_attention": assets,
        "boundary": "专家观点仅作为研究关注度 sidecar，不修改当前 Decision Matrix directional composite。",
    }
    sources = flash.setdefault("sources", {})
    sources["bidclub_expert_intelligence"] = intel.get("generated_at") if isinstance(intel, dict) else None
    quality = flash.setdefault("quality", {})
    quality["bidclub_expert_intelligence"] = {
        "status": intel.get("status", "missing") if isinstance(intel, dict) else "missing",
        "episodes_scanned": (intel.get("summary") or {}).get("episodes_scanned") if isinstance(intel, dict) else 0,
        "relevant_insights": (intel.get("summary") or {}).get("relevant_insights") if isinstance(intel, dict) else 0,
        "mapped_assets": (intel.get("summary") or {}).get("mapped_assets") if isinstance(intel, dict) else 0,
        "warnings": len(intel.get("warnings", [])) if isinstance(intel, dict) else 1,
    }
    return flash


def main():
    flash = load(FLASH_PATH)
    if not flash:
        raise SystemExit("daily_flash.json missing or invalid")
    intel = load(INTEL_PATH)
    attach(flash, intel)
    tmp = FLASH_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(flash, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(tmp, FLASH_PATH)
    print("attached BidClub intelligence", flash.get("expert_intelligence", {}).get("summary", {}))


if __name__ == "__main__":
    main()
