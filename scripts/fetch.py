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

KEYWORD_RULES = [
    ("亚马逊", ("amazon", "aws", "亚马逊")),
    ("微软", ("microsoft", "azure", "微软")),
    ("谷歌", ("google", "alphabet", "谷歌")),
    ("Meta", ("meta platforms", "facebook", "元宇宙平台")),
    ("英伟达", ("nvidia", "英伟达")),
    ("美光", ("micron", "美光")),
    ("三星电子", ("samsung electronics", "samsung", "三星电子")),
    ("SK海力士", ("sk hynix", "hynix", "sk海力士", "海力士")),
    ("苹果", ("apple", "iphone", "苹果")),
    ("台积电", ("tsmc", "taiwan semiconductor", "台积电")),
    ("长鑫科技", ("cxmt", "changxin", "长鑫科技", "长鑫存储")),
    ("人工智能", ("artificial intelligence", " ai ", "人工智能")),
    ("云计算", ("cloud computing", "cloud services", "aws", "azure", "云计算")),
    ("数据中心", ("data center", "datacenter", "数据中心")),
    ("AI资本开支", ("ai capex", "capital expenditure", "capital spending", "资本开支")),
    ("光模块", ("optical transceiver", "optical module", "800g", "1.6t", "cpo", "光模块")),
    ("PCB", ("printed circuit board", " pcb ", "印制电路板")),
    ("DRAM", ("dram",)),
    ("NAND", ("nand",)),
    ("存储芯片", ("memory chip", "memory semiconductor", "memory market", "存储芯片")),
    ("晶圆代工", ("foundry", "wafer fab", "晶圆代工")),
    ("先进封装", ("advanced packaging", "chip packaging", "先进封装")),
    ("半导体设备", ("semiconductor equipment", "chip equipment", "半导体设备")),
    ("MLCC", ("mlcc", "multilayer ceramic capacitor")),
    ("被动元件", ("passive component", "被动元件")),
    ("消费电子", ("consumer electronics", "smartphone", "iphone", "消费电子")),
    ("新能源汽车", ("electric vehicle", " ev ", "新能源汽车")),
    ("机器人", ("robotics", "robot", "机器人")),
    ("创新药", ("biotech", "drug trial", "clinical trial", "创新药")),
    ("黄金", ("gold", "黄金")),
    ("白银", ("silver", "白银")),
    ("美联储", ("federal reserve", "fed rate", "fomc", "美联储")),
]

EVENT_RULES = [
    ("资本开支上调", ("raise capital spending", "boost capital spending", "boost spending", "capex increase",
                  "capital expenditure plan", "capital spending plan")),
    ("业绩超预期", ("beats estimates", "beat expectations", "record profit",
                "record revenue", "surges after earnings")),
    ("业绩承压", ("misses estimates", "missed expectations", "profit warning",
              "revenue decline", "profit falls", "profit drops")),
    ("扩产", ("expand capacity", "capacity expansion", "new fab", "new factory")),
    ("涨价", ("price increase", "raise prices", "price hike", "prices rise")),
    ("降价", ("price cut", "cuts prices", "prices fall", "price decline")),
    ("并购", ("acquisition", "acquire", "merger", "takeover")),
    ("出口限制", ("export control", "export restriction", "sanction", "blacklist")),
    ("政策变化", ("regulation", "policy change", "government subsidy")),
]


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


def contains_pattern(blob, pattern):
    pattern = pattern.lower()
    if pattern.startswith(" ") or pattern.endswith(" ") or re.fullmatch(r"[a-z0-9.]+", pattern):
        return pattern.strip() in re.findall(r"[a-z0-9.]+", blob)
    return pattern in blob


def matched_label(blob, rules):
    for label, patterns in rules:
        if any(contains_pattern(blob, pattern) for pattern in patterns):
            return label
    return ""


def extract_keywords_zh(item, industry_name):
    blob = " %s %s " % (item.get("title", "").lower(), item.get("summary", "").lower())
    labels = []
    for label, patterns in KEYWORD_RULES:
        if any(contains_pattern(blob, pattern) for pattern in patterns) and label not in labels:
            labels.append(label)
        if len(labels) >= 3:
            break
    event_type = matched_label(blob, EVENT_RULES)
    if event_type and event_type not in labels:
        labels.append(event_type)
    if not labels and industry_name:
        labels.append(industry_name)
    return labels[:4], event_type


def asset_match_points(item, asset):
    title = item.get("title", "").lower()
    summary = item.get("summary", "").lower()
    points = 0
    for keyword in asset.get("keywords", []):
        term = keyword.lower()
        if contains_pattern(title, term):
            points += 3
        elif contains_pattern(summary, term):
            points += 1
    return points


def enrich_items(industries, watchlist):
    assets = watchlist.get("assets", [])
    for industry in industries:
        for item in industry.get("items", []):
            keywords_zh, event_type = extract_keywords_zh(item, industry.get("name", ""))
            matches = []
            for asset in assets:
                if industry.get("key") not in asset.get("industries", []):
                    continue
                points = asset_match_points(item, asset)
                if points:
                    matches.append((points, asset))
            matches.sort(key=lambda row: (-row[0], -row[1].get("priority", 0)))
            event_boost = 2 if event_type else 0
            best_points = matches[0][0] if matches else 0
            priority_boost = matches[0][1].get("priority", 0) // 2 if matches else 0
            item["keywords_zh"] = keywords_zh
            item["event_type"] = event_type
            item["related_assets"] = [row[1]["name"] for row in matches[:3]]
            item["relevance_score"] = (
                min(10, best_points + priority_boost + event_boost) if matches else 0
            )


def build_watchlist(industries, watchlist):
    """Keep the personalized radar useful even when no LLM key is configured."""
    related_counts = {}
    for industry in industries:
        for item in industry.get("items", []):
            for name in item.get("related_assets", []):
                related_counts[name] = related_counts.get(name, 0) + 1
    output = []
    for asset in watchlist.get("assets", []):
        row = dict(asset)
        row["news_hits"] = related_counts.get(asset["name"], 0)
        output.append(row)
    return sorted(output, key=lambda row: (-row.get("news_hits", 0), -row.get("priority", 0)))


def main():
    global CUTOFF, REDLINE, PER_SOURCE, TIMEOUT
    cfg = json.load(open(os.path.join(ROOT, "sources.json"), encoding="utf-8"))
    watchlist = json.load(open(os.path.join(ROOT, "watchlist.json"), encoding="utf-8"))
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
    enrich_items(industries, watchlist)

    data = {
        "generated_at": datetime.now(BEIJING).strftime("%Y-%m-%d %H:%M"),
        "recent_days": days,
        "industries": industries,
        "signals": [],
        "watchlist": build_watchlist(industries, watchlist),
        "profile": watchlist.get("profile", {}),
        "decision_rules": watchlist.get("decision_rules", {}),
        "has_ai": False,
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
