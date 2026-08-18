#!/usr/bin/env python3
"""Fill A-share breadth from Sina only when the primary market-state source failed.

AKShare documents ``stock_zh_a_spot`` as a full Shanghai/Shenzhen/Beijing
A-share realtime snapshot from Sina. It is deliberately used only as a fallback
to avoid unnecessary repeated requests and rate limiting.
"""

from __future__ import annotations

import os

from fetch_market_state import (
    OUTPUT,
    atomic_write,
    breadth_from_rows,
    load_json,
    score_regime,
    _to_records,
)


def main():
    payload = load_json(OUTPUT)
    if (payload.get("section_status", {}).get("breadth") or {}).get("status") == "fresh":
        print("breadth primary source already fresh; fallback skipped")
        return

    try:
        import akshare as ak
        rows = _to_records(ak.stock_zh_a_spot())
        breadth = breadth_from_rows(rows)
        if breadth.get("total", 0) < 1000:
            raise RuntimeError(f"Sina returned only {breadth.get('total', 0)} usable A-share rows")
    except Exception as exc:
        payload.setdefault("warnings", []).append(f"breadth_sina_fallback: {exc}")
        atomic_write(payload)
        print("warning: breadth Sina fallback failed:", exc)
        return

    payload["breadth"] = breadth
    payload.setdefault("section_status", {})["breadth"] = {
        "status": "fresh",
        "source": "新浪财经 via AKShare",
        "fallback": True,
    }
    payload["regime"] = score_regime(breadth, payload.get("indices") or [])
    payload.setdefault("warnings", []).append("breadth primary source unavailable; using 新浪财经 via AKShare fallback")
    payload.setdefault("methodology", {})["breadth_source"] = "东方财富主源；失败时单次回退新浪财经 AKShare stock_zh_a_spot。"
    atomic_write(payload)
    print("breadth fallback", breadth.get("total"), payload["regime"])


if __name__ == "__main__":
    main()
