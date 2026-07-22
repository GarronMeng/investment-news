#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取 RSS/Atom，执行时效过滤、红线过滤和确定性去重，写入 data.js。"""
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BEIJING = timezone(timedelta(hours=8))
CUTOFF = None
REDLINE = []
PER_SOURCE = 6
TIMEOUT = 15


def strip_html(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value or "")).strip()


def local(tag):
    return tag.split("}")[-1]


def parse_dt(value):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
    except Exception:
        try:
            dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except Exception:
            return None
    if dt and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def normalize_title(title):
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", (title or "").lower())
    return text[:140]


def canonical_url(url):
    try:
        p = urllib.parse.urlsplit(url or "")
        clean = urllib.parse.urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip("/"), "", ""))
        return clean
    except Exception:
        return url or ""


def fetch_source(src):
    try:
        req = urllib.request.Request(src["url"], headers={
            "User-Agent": UA,
            "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,*/*"
        })
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            raw = response.read()
        root = ET.fromstring(raw)
        out = []
        for node in [e for e in root.iter() if local(e.tag) in ("item", "entry")]:
            if len(out) >= PER_SOURCE:
                break
            item = {"title": "", "url": "", "time": "", "ts": 0,
                    "summary": "", "source": src["name"]}
            raw_time = ""
            for child in node:
                tag = local(child.tag)
                if tag == "title" and not item["title"]:
                    item["title"] = (child.text or "").strip()
                elif tag == "link" and not item["url"]:
                    item["url"] = child.get("href") or (child.text or "").strip()
                elif tag in ("pubDate", "published", "updated", "date") and not raw_time:
                    raw_time = (child.text or "").strip()
                elif tag in ("description", "summary", "content") and not item["summary"]:
                    item["summary"] = strip_html(child.text or "")[:240]
            if not item["title"]:
                continue
            blob = (item["title"] + " " + item["summary"]).lower()
            if any(keyword in blob for keyword in REDLINE):
                continue
            dt = parse_dt(raw_time)
            if dt is not None:
                if CUTOFF and dt < CUTOFF:
                    continue
                item["time"] = dt.astimezone(BEIJING).strftime("%m-%d %H:%M")
                item["ts"] = int(dt.timestamp())
            else:
                item["time"] = "—"
            item["url"] = canonical_url(item["url"])
            fingerprint = normalize_title(item["title"]) or item["url"]
            item["id"] = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:12]
            out.append(item)
        return out
    except Exception as exc:
        print("  ⚠️ 源抓取失败 %s: %s" % (src.get("name", "?"), str(exc)[:100]))
        return None


def deduplicate(items):
    seen_urls, seen_titles, output = set(), set(), []
    for item in sorted(items, key=lambda x: x.get("ts", 0), reverse=True):
        url_key = canonical_url(item.get("url", ""))
        title_key = normalize_title(item.get("title", ""))
        if url_key and url_key in seen_urls:
            continue
        if title_key and title_key in seen_titles:
            continue
        if url_key:
            seen_urls.add(url_key)
        if title_key:
            seen_titles.add(title_key)
        output.append(item)
    return output


def main():
    global CUTOFF, REDLINE, PER_SOURCE, TIMEOUT
    cfg = json.load(open(os.path.join(ROOT, "sources.json"), encoding="utf-8"))
    fetch_cfg = cfg.get("fetch", {})
    days = int(fetch_cfg.get("recent_days", 3))
    PER_SOURCE = int(fetch_cfg.get("per_source", 8))
    TIMEOUT = int(fetch_cfg.get("timeout", 15))
    CUTOFF = datetime.now(timezone.utc) - timedelta(days=days)
    REDLINE = [k.lower() for k in cfg.get("redline_keywords", [])]

    by_hint = {}
    for source in cfg["sources"]:
        by_hint.setdefault(source["hint"], []).append(source)

    industries, tasks = [], []
    for idx, industry in enumerate(cfg["industries"]):
        pool = by_hint.get(industry["key"], [])
        industries.append({"key": industry["key"], "name": industry["name"],
                           "accent": industry["accent"], "total": len(pool), "items": []})
        tasks.extend((idx, source) for source in pool)

    workers = min(32, max(4, len(tasks)))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(lambda task: (task[0], task[1].get("name", ""), fetch_source(task[1])), tasks))

    failed = []
    for idx, name, items in results:
        if items is None:
            failed.append(name)
        else:
            industries[idx]["items"].extend(items)

    raw_count = 0
    unique_count = 0
    for industry in industries:
        raw_count += len(industry["items"])
        industry["items"] = deduplicate(industry["items"])
        unique_count += len(industry["items"])

    data = {
        "generated_at": datetime.now(BEIJING).strftime("%Y-%m-%d %H:%M"),
        "recent_days": days,
        "industries": industries,
        "signals": [],
        "watchlist": [],
        "stats": {
            "industries": len(industries),
            "total_sources": len(cfg["sources"]),
            "raw_items": raw_count,
            "unique_items": unique_count,
            "failed_sources": len(failed)
        }
    }
    path = os.path.join(ROOT, "data.js")
    with open(path, "w", encoding="utf-8") as output:
        output.write("// 自动生成，请勿手工编辑。\n")
        output.write("window.DATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")

    print("最近 %d 天，抓取 %d 条，去重后 %d 条，失败源 %d 个。" %
          (days, raw_count, unique_count, len(failed)))
    if failed:
        print("失败源：" + "、".join(failed[:20]))


if __name__ == "__main__":
    main()
