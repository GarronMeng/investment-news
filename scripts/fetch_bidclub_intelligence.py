#!/usr/bin/env python3
"""Fetch BidClub editorial intelligence and map it to the local watchlist.

This is deliberately a sidecar research layer. It raises research attention when
relevant expert commentary appears, but it does not directly alter the existing
bullish/bearish Decision Matrix composite score.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "bidclub_config.json")
WATCHLIST_PATH = os.path.join(ROOT, "watchlist.json")
OUTPUT_PATH = os.path.join(ROOT, "expert_intelligence.json")
BEIJING = timezone(timedelta(hours=8))
USER_AGENT = "investment-news-bidclub/1.0 (+https://github.com/GarronMeng/investment-news)"


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {} if default is None else default


def atomic_write(payload, path=OUTPUT_PATH):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(tmp, path)


def http_json(url, timeout=20):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_datetime(value):
    if not value:
        return None
    text = str(value).strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=BEIJING)
        return dt.astimezone(BEIJING)
    except ValueError:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d").replace(tzinfo=BEIJING)
        except ValueError:
            return None


def normalize_text(*parts):
    return "\n".join(str(part or "") for part in parts).casefold()


def keyword_hits(text, keywords):
    hits = []
    for keyword in keywords or []:
        token = str(keyword or "").strip()
        if token and token.casefold() in text:
            hits.append(token)
    return list(dict.fromkeys(hits))


def markdown_excerpt(text, limit=1800):
    value = str(text or "").strip()
    value = re.sub(r"\n{3,}", "\n\n", value)
    if len(value) <= limit:
        return value
    cut = value[:limit]
    boundary = max(cut.rfind("。"), cut.rfind(". "), cut.rfind("\n"))
    if boundary >= int(limit * 0.65):
        cut = cut[: boundary + 1]
    return cut.rstrip() + "…"


def trigger_hits(text, triggers):
    # Transparent but conservative: exact phrase/subphrase matching only.
    hits = []
    for phrase in triggers or []:
        phrase_text = str(phrase or "").strip()
        if not phrase_text:
            continue
        lowered = phrase_text.casefold()
        if lowered in text:
            hits.append(phrase_text)
            continue
        tokens = [token for token in re.split(r"[\s、，,/]+", lowered) if len(token) >= 3]
        if tokens and all(token in text for token in tokens[:2]):
            hits.append(phrase_text)
    return list(dict.fromkeys(hits))


def asset_map(watchlist):
    return {str(row.get("code")): row for row in watchlist.get("assets", []) if row.get("code")}


def map_episode(detail, watchlist, config, now):
    title = detail.get("title") or ""
    tldr = detail.get("tldr_md") or detail.get("tldr_md_alt") or ""
    digest = detail.get("digest_md") or detail.get("digest_md_alt") or ""
    dek = detail.get("dek") or detail.get("dek_alt") or ""
    text = normalize_text(title, dek, tldr, digest)
    assets = asset_map(watchlist)

    topic_rows = []
    mapped_codes = set()
    topic_match_count = 0
    for topic in config.get("topics", []):
        hits = keyword_hits(text, topic.get("keywords"))
        if not hits:
            continue
        topic_match_count += len(hits)
        codes = [str(code) for code in topic.get("assets", []) if str(code) in assets]
        mapped_codes.update(codes)
        topic_rows.append({
            "id": topic.get("id"),
            "label": topic.get("label"),
            "hits": hits[:8],
            "assets": codes,
        })

    direct_rows = []
    for code, asset in assets.items():
        hits = keyword_hits(text, [asset.get("name"), *(asset.get("keywords") or [])])
        if not hits:
            continue
        mapped_codes.add(code)
        direct_rows.append({"code": code, "name": asset.get("name"), "hits": hits[:10]})

    if not mapped_codes:
        return None

    published = parse_datetime(detail.get("published_at") or detail.get("date"))
    age_days = (now - published).total_seconds() / 86400 if published else 30.0
    age_days = max(0.0, age_days)
    direct_hits = sum(len(row["hits"]) for row in direct_rows)
    unique_topics = len(topic_rows)
    numeric_specificity = min(10, len(re.findall(r"(?<!\w)\d+(?:\.\d+)?%?|\$\d+(?:\.\d+)?", f"{tldr}\n{digest}")))

    relevance = min(55, direct_hits * 9 + topic_match_count * 4 + unique_topics * 5)
    recency = max(0, 20 - min(20, age_days * 1.5))
    specificity = min(15, 4 + numeric_specificity + min(5, unique_topics * 2))
    provenance = 10 if detail.get("source_url") or detail.get("youtube_url") else 5
    score = round(min(100, relevance + recency + specificity + provenance), 1)
    if score < float(config.get("minimum_relevance_score", 18)):
        return None

    per_asset = []
    direct_by_code = {row["code"]: row for row in direct_rows}
    for code in sorted(mapped_codes):
        asset = assets[code]
        positive = trigger_hits(text, asset.get("positive_triggers"))
        negative = trigger_hits(text, asset.get("negative_triggers"))
        if positive and not negative:
            stance = "positive_candidate"
        elif negative and not positive:
            stance = "negative_candidate"
        elif positive and negative:
            stance = "mixed_candidate"
        else:
            stance = "review_required"
        topic_hits_for_asset = []
        for row in topic_rows:
            if code in row["assets"]:
                topic_hits_for_asset.extend(row["hits"])
        direct_hits_for_asset = (direct_by_code.get(code) or {}).get("hits", [])
        local_score = min(100, score + min(12, len(direct_hits_for_asset) * 4 + len(topic_hits_for_asset)))
        per_asset.append({
            "code": code,
            "name": asset.get("name"),
            "relevance_score": round(local_score, 1),
            "stance": stance,
            "direct_hits": direct_hits_for_asset[:10],
            "topic_hits": list(dict.fromkeys(topic_hits_for_asset))[:10],
            "positive_trigger_hits": positive[:4],
            "negative_trigger_hits": negative[:4],
        })

    slug = detail.get("slug")
    return {
        "slug": slug,
        "show_id": detail.get("show_id"),
        "show": (detail.get("shows") or {}).get("name"),
        "title": title,
        "date": detail.get("date"),
        "published_at": detail.get("published_at"),
        "duration_min": detail.get("duration_min"),
        "people": [chip[7:] for chip in detail.get("chips", []) if isinstance(chip, str) and chip.startswith("person:")],
        "score": score,
        "topics": topic_rows,
        "assets": per_asset,
        "tldr": markdown_excerpt(tldr, 1200),
        "digest_excerpt": markdown_excerpt(digest, 2200),
        "bidclub_url": f"https://bidclub.ai/e/{slug}" if slug else None,
        "source_url": detail.get("source_url") or detail.get("youtube_url") or detail.get("rss_url"),
        "provenance": detail.get("provenance"),
        "transcript_available": bool(detail.get("transcript_md")),
    }


def build_asset_overlay(insights, watchlist, config):
    assets = asset_map(watchlist)
    grouped = {code: [] for code in assets}
    for insight in insights:
        for mapped in insight.get("assets", []):
            code = str(mapped.get("code"))
            if code in grouped:
                grouped[code].append({
                    "slug": insight.get("slug"),
                    "title": insight.get("title"),
                    "show": insight.get("show"),
                    "published_at": insight.get("published_at") or insight.get("date"),
                    "score": mapped.get("relevance_score"),
                    "stance": mapped.get("stance"),
                    "bidclub_url": insight.get("bidclub_url"),
                    "trigger_hits": {
                        "positive": mapped.get("positive_trigger_hits", []),
                        "negative": mapped.get("negative_trigger_hits", []),
                    },
                })

    result = {}
    limit = int(config.get("max_insights_per_asset", 5))
    for code, rows in grouped.items():
        rows.sort(key=lambda row: (-(row.get("score") or 0), str(row.get("published_at") or "")), reverse=False)
        rows = rows[:limit]
        if not rows:
            continue
        top_score = max(float(row.get("score") or 0) for row in rows)
        attention_boost = round(min(15.0, 2.0 + len(rows) * 2.0 + top_score / 20.0), 1)
        stances = {row.get("stance") for row in rows}
        if stances == {"positive_candidate"}:
            stance_summary = "positive_candidate"
        elif stances == {"negative_candidate"}:
            stance_summary = "negative_candidate"
        elif "positive_candidate" in stances and "negative_candidate" in stances:
            stance_summary = "mixed_candidate"
        else:
            stance_summary = "review_required"
        result[code] = {
            "code": code,
            "name": assets[code].get("name"),
            "attention_boost": attention_boost,
            "stance_summary": stance_summary,
            "insight_count": len(rows),
            "top_relevance_score": round(top_score, 1),
            "insights": rows,
        }
    return result


def degraded_payload(now, warning):
    return {
        "version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "source": "BidClub",
        "status": "degraded",
        "summary": {"episodes_scanned": 0, "relevant_insights": 0, "mapped_assets": 0},
        "insights": [],
        "assets": {},
        "warnings": [warning],
        "methodology": {
            "role": "expert opinion sidecar",
            "directional_use": "disabled for composite scoring",
        },
        "boundary": "外部专家观点仅用于提高研究关注度；未通过原始来源与硬数据交叉验证前，不进入方向性综合评分。",
    }


def fetch_payload(config, watchlist, now=None):
    now = now or datetime.now(BEIJING)
    if not config.get("enabled", True):
        return degraded_payload(now, "BidClub integration disabled in configuration.")
    base = str(config.get("base_url") or "https://bidclub.ai").rstrip("/")
    limit = max(1, min(100, int(config.get("max_episode_metadata", 100))))
    metadata_url = f"{base}/api/v1/episodes?limit={limit}"
    collection = http_json(metadata_url)
    episodes = collection.get("episodes", []) if isinstance(collection, dict) else []
    lookback = timedelta(days=float(config.get("lookback_days", 14)))
    recent = []
    for row in episodes:
        published = parse_datetime(row.get("published_at") or row.get("date"))
        if published is None or now - published <= lookback:
            recent.append(row)
    recent = recent[: max(1, int(config.get("max_episode_details", 40)))]

    insights = []
    warnings = []
    for row in recent:
        slug = row.get("slug")
        if not slug:
            continue
        url = f"{base}/api/v1/episodes/{urllib.parse.quote(str(slug), safe='')}"
        try:
            detail = http_json(url)
            mapped = map_episode(detail, watchlist, config, now)
            if mapped:
                insights.append(mapped)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            warnings.append(f"{slug}: {type(exc).__name__}")
        time.sleep(0.03)

    insights.sort(key=lambda row: (-(row.get("score") or 0), str(row.get("published_at") or row.get("date") or "")))
    insights = insights[: int(config.get("max_insights", 20))]
    overlay = build_asset_overlay(insights, watchlist, config)
    return {
        "version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "source": "BidClub",
        "source_api": f"{base}/api-docs",
        "status": "ok" if not warnings else "partial",
        "summary": {
            "episodes_scanned": len(recent),
            "relevant_insights": len(insights),
            "mapped_assets": len(overlay),
            "warnings": len(warnings),
        },
        "insights": insights,
        "assets": overlay,
        "warnings": warnings[:20],
        "methodology": {
            "role": "专家/产业观点 sidecar；补充新闻与行情无法直接提供的 thesis evidence。",
            "content_used": "title + dek + BidClub TL;DR + digest；默认不把完整 transcript 写入仓库。",
            "relevance": "watchlist 关键词 + 主题映射 + 时效性 + 数字/来源具体度；0-100 仅表示研究相关性，不表示上涨概率。",
            "stance": "仅对 watchlist 预先定义的正/负触发词做保守匹配；无法清晰匹配时强制 review_required。",
            "attention_boost": "0-15 的研究关注度增量；第一版不进入 Decision Matrix directional composite。",
            "provenance": "保留 BidClub episode URL 与原始 source URL，供回看全文/录音验证。",
        },
        "boundary": "专家观点属于软证据。任何 bullish/negative candidate 都必须与公告、财报、产业硬数据和价格行为交叉验证；本文件不生成买卖、仓位、止损或目标价。",
    }


def main():
    config = load_json(CONFIG_PATH)
    watchlist = load_json(WATCHLIST_PATH)
    now = datetime.now(BEIJING)
    try:
        payload = fetch_payload(config, watchlist, now=now)
    except Exception as exc:  # external source must never break the core pipeline
        payload = degraded_payload(now, f"BidClub fetch failed: {type(exc).__name__}: {exc}")
    atomic_write(payload)
    print("bidclub", payload.get("status"), payload.get("summary"), "warnings", len(payload.get("warnings", [])))


if __name__ == "__main__":
    main()
