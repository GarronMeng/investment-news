#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取 RSS/Atom，聚合同事件、维护轨迹，并写入 data.js/history.json。"""
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
HISTORY_DAYS = 14
HISTORY_LIMIT = 24
WINDOW_SECONDS = 6 * 3600

PRIMARY_SOURCES = {
    "OpenAI", "Google Research", "Hugging Face", "DeepMind", "BAIR Blog",
    "arXiv cs.AI", "NASA", "SEC", "Federal Reserve", "GitHub Blog",
}
MARKET_SOURCES = {
    "CNBC", "Financial Times", "WSJ Markets", "MarketWatch", "Yahoo Finance",
    "华尔街见闻", "东方财富股票", "东方财富资讯", "经济观察网", "Seeking Alpha",
}
TRADE_SOURCE_MARKERS = (
    "Semiconductor", "SemiAnalysis", "DIGITIMES", "EE Times", "Electronics",
    "BioPharma", "Fierce", "Energy", "Robot", "PV ", "pv magazine",
)

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
                  "capital expenditure plan", "capital spending plan", "上调资本开支", "增加资本开支")),
    ("业绩超预期", ("beats estimates", "beat expectations", "record profit",
                "record revenue", "surges after earnings")),
    ("业绩承压", ("misses estimates", "missed expectations", "profit warning",
              "revenue decline", "profit falls", "profit drops")),
    ("扩产", ("expand capacity", "capacity expansion", "new fab", "new factory", "扩产", "新建工厂")),
    ("涨价", ("price increase", "raise prices", "price hike", "prices rise", "涨价", "上调价格")),
    ("降价", ("price cut", "cuts prices", "prices fall", "price decline", "降价")),
    ("并购", ("acquisition", "acquire", "merger", "takeover", "收购", "合并")),
    ("出口限制", ("export control", "export restriction", "sanction", "blacklist", "出口限制", "制裁")),
    ("政策变化", ("regulation", "policy change", "government subsidy", "政策调整", "补贴政策")),
    ("产品发布", ("launches", "unveils", "announces new", "product launch", "发布", "推出")),
]


def detect_language(text):
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text or ""))
    latin = len(re.findall(r"[A-Za-z]", text or ""))
    return "zh" if cjk >= max(2, latin // 5) else "en"


def classify_agenda(source):
    if source in PRIMARY_SOURCES:
        return "primary"
    if source in MARKET_SOURCES:
        return "market"
    if any(marker.lower() in source.lower() for marker in TRADE_SOURCE_MARKERS):
        return "industry"
    return "media"


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
                    "summary": "", "source": src["name"],
                    "agenda_layer": src.get("agenda") or classify_agenda(src["name"])}
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
            item["language"] = src.get("language") or detect_language(
                item["title"] + " " + item["summary"]
            )
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
            item["topic_id"] = topic_id(item, industry.get("key", ""), industry.get("name", ""))


def topic_id(item, industry_key, industry_name):
    """Use canonical Chinese labels to bridge Chinese/English coverage conservatively."""
    event_type = item.get("event_type", "")
    anchors = [
        label for label in item.get("keywords_zh", [])
        if label not in (event_type, industry_name)
    ]
    if not event_type or not anchors:
        return "story:" + item.get("id", "")
    seed = "%s|%s|%s" % (industry_key, event_type, "|".join(sorted(anchors[:2])))
    return "topic:" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def title_similarity(left, right):
    def tokens(text):
        words = set(re.findall(r"[a-z0-9]{3,}|[\u4e00-\u9fff]{2}", (text or "").lower()))
        return words - {"the", "and", "for", "with", "from", "that", "this", "will", "into"}
    a, b = tokens(left), tokens(right)
    return len(a & b) / max(1, len(a | b))


def merge_event_clusters(industries):
    """Collapse only stories that share both a canonical anchor and a material event."""
    for industry in industries:
        clusters = []
        for item in sorted(industry.get("items", []), key=lambda row: row.get("ts", 0), reverse=True):
            topic = item.get("topic_id") or "story:" + item["id"]
            target = None
            for cluster in clusters:
                first = cluster[0]
                same_topic = topic.startswith("topic:") and topic == first.get("topic_id")
                same_language_story = (
                    topic.startswith("story:")
                    and item.get("language") == first.get("language")
                    and abs(item.get("ts", 0) - first.get("ts", 0)) <= 36 * 3600
                    and title_similarity(item.get("title", ""), first.get("title", "")) >= .52
                )
                if same_topic or same_language_story:
                    target = cluster
                    break
            if target is None:
                clusters.append([item])
            else:
                target.append(item)
        merged = []
        for rows in clusters:
            rows.sort(key=lambda row: row.get("ts", 0), reverse=True)
            representative = dict(rows[0])
            representative["cluster_size"] = len(rows)
            representative["sources"] = sorted({row.get("source", "") for row in rows if row.get("source")})
            representative["languages"] = sorted({row.get("language", "") for row in rows if row.get("language")})
            representative["agenda_layers"] = sorted({row.get("agenda_layer", "") for row in rows if row.get("agenda_layer")})
            representative["cluster_urls"] = [
                {"source": row.get("source", ""), "title": row.get("title", ""), "url": row.get("url", "")}
                for row in rows[:6]
            ]
            representative["related_assets"] = list(dict.fromkeys(
                name for row in rows for name in row.get("related_assets", [])
            ))[:4]
            representative["relevance_score"] = max(row.get("relevance_score", 0) for row in rows)
            merged.append(representative)
        industry["items"] = sorted(merged, key=lambda row: row.get("ts", 0), reverse=True)


def load_history(path):
    try:
        with open(path, encoding="utf-8") as stream:
            data = json.load(stream)
        return data if isinstance(data.get("topics"), dict) else {"version": 1, "topics": {}}
    except (OSError, ValueError, TypeError):
        return {"version": 1, "topics": {}}


def trajectory_label(points, now_ts):
    if len(points) == 1:
        return "new"
    current, previous = points[-1], points[-2]
    gap_hours = (current["ts"] - previous["ts"]) / 3600
    rank_gain = previous.get("rank", 99) - current.get("rank", 99)
    source_gain = current.get("source_count", 1) - previous.get("source_count", 1)
    age_hours = (now_ts - points[0]["ts"]) / 3600
    if gap_hours >= 18:
        return "rebound"
    if rank_gain >= 3 or source_gain >= 2:
        return "surge"
    if rank_gain <= -3 or source_gain <= -2:
        return "decay"
    if age_hours >= 72 and len(points) >= 4 and abs(points[0].get("rank", 99) - current.get("rank", 99)) <= 2:
        return "zombie"
    return "steady"


def update_history(industries, history, now_ts=None):
    now_ts = int(now_ts or datetime.now(timezone.utc).timestamp())
    topics = history.setdefault("topics", {})
    for industry in industries:
        for rank, item in enumerate(industry.get("items", []), start=1):
            key = item.get("topic_id") or "story:" + item.get("id", "")
            entry = topics.setdefault(key, {
                "first_seen": now_ts, "last_seen": now_ts, "industry": industry.get("key", ""),
                "title": item.get("title", ""), "points": []
            })
            snapshot = {
                "ts": now_ts,
                "rank": rank,
                "source_count": len(item.get("sources", [])) or 1,
                "sources": item.get("sources", [item.get("source", "")]),
                "languages": item.get("languages", [item.get("language", "")]),
                "agenda_layers": item.get("agenda_layers", [item.get("agenda_layer", "")]),
            }
            points = entry.setdefault("points", [])
            if points and now_ts - points[-1].get("ts", 0) < 1800:
                points[-1] = snapshot
            else:
                points.append(snapshot)
            entry["points"] = points[-HISTORY_LIMIT:]
            entry["last_seen"] = now_ts
            recent = entry["points"]
            all_sources = sorted({source for point in recent for source in point.get("sources", []) if source})
            all_languages = sorted({lang for point in recent for lang in point.get("languages", []) if lang})
            all_agendas = sorted({layer for point in recent for layer in point.get("agenda_layers", []) if layer})
            windows = len({point["ts"] // WINDOW_SECONDS for point in recent})
            item["trajectory"] = {
                "label": trajectory_label(recent, now_ts),
                "points": [point.get("rank", 0) for point in recent[-8:]],
                "observations": len(recent),
                "first_seen": entry.get("first_seen", now_ts),
            }
            item["resonance"] = {
                "confirmed": len(all_sources) >= 2 and len(all_languages) >= 2 and len(all_agendas) >= 2 and windows >= 2,
                "source_count": len(all_sources),
                "languages": all_languages,
                "agenda_layers": all_agendas,
                "time_windows": windows,
            }
    cutoff = now_ts - HISTORY_DAYS * 86400
    history["topics"] = {
        key: value for key, value in topics.items() if value.get("last_seen", 0) >= cutoff
    }
    history["updated_at"] = datetime.fromtimestamp(now_ts, BEIJING).strftime("%Y-%m-%d %H:%M")
    return history


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
    return sorted(output, key=lambda row: (row.get("display_order", 999), -row.get("priority", 0)))


def is_trajectory_signal(item):
    """Match the dashboard rule: a snapshot alone is not a change signal."""
    trajectory = item.get("trajectory", {})
    label = trajectory.get("label")
    points = [value for value in trajectory.get("points", []) if isinstance(value, (int, float))]
    resonance = item.get("resonance", {})
    sources = resonance.get("source_count", item.get("cluster_size", 1)) or 1
    if not label or label == "steady":
        return False
    if label == "new":
        return sources >= 2 and (
            item.get("relevance_score", 0) >= 5 or resonance.get("confirmed", False)
        )
    return len(points) >= 2 and (
        item.get("relevance_score", 0) > 0 or resonance.get("confirmed", False)
    )


def history_progress(history):
    topics = history.get("topics", {})
    timestamps = sorted({
        point.get("ts")
        for topic in topics.values()
        for point in topic.get("points", [])
        if point.get("ts")
    })
    eligible = sum(len(topic.get("points", [])) >= 2 for topic in topics.values())
    return {
        "updated_at": history.get("updated_at"),
        "sampling_windows": len(timestamps),
        "previous_sample_at": (
            datetime.fromtimestamp(timestamps[-2], BEIJING).strftime("%Y-%m-%d %H:%M")
            if len(timestamps) >= 2 else None
        ),
        "latest_sample_at": (
            datetime.fromtimestamp(timestamps[-1], BEIJING).strftime("%Y-%m-%d %H:%M")
            if timestamps else None
        ),
        "tracked_topics": len(topics),
        "comparable_topics": eligible,
        "coalesce_minutes": 30,
    }


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
    merge_event_clusters(industries)
    history_path = os.path.join(ROOT, "history.json")
    history = update_history(industries, load_history(history_path))

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
            "failed_sources": len(failed),
            "event_cards": sum(len(industry.get("items", [])) for industry in industries),
            "trajectory_signals": sum(
                1 for industry in industries for item in industry.get("items", [])
                if is_trajectory_signal(item)
            ),
            "history": history_progress(history),
        }
    }
    path = os.path.join(ROOT, "data.js")
    with open(path, "w", encoding="utf-8") as output:
        output.write("// 自动生成，请勿手工编辑。\n")
        output.write("window.DATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
    with open(history_path, "w", encoding="utf-8") as output:
        json.dump(history, output, ensure_ascii=False, indent=1)
        output.write("\n")

    print("最近 %d 天，抓取 %d 条，去重后 %d 条，失败源 %d 个。" %
          (days, raw_count, unique_count, len(failed)))
    if failed:
        print("失败源：" + "、".join(failed[:20]))


if __name__ == "__main__":
    main()
