#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import base64
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "scripts" / "sources.yaml"
COLLECTED_DIR = ROOT / "data" / "collected"


@dataclass
class CollectContext:
    config: dict[str, Any]
    logs: list[str]

    @property
    def timeout(self) -> int:
        return int(self.config.get("request", {}).get("timeout_seconds", 12))

    @property
    def delay(self) -> float:
        return float(self.config.get("request", {}).get("delay_seconds", 0.6))

    @property
    def user_agent(self) -> str:
        return str(self.config.get("request", {}).get("user_agent", "IndustrialDesignIntelligenceBot/0.1"))


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def clean_text(value: str | None, max_length: int = 320) -> str:
    if not value:
        return ""
    text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_length]


def stable_id(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def domain_name(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except ValueError:
        return ""


def unwrap_bing_url(url: str) -> str:
    parsed = urlparse(url)
    if "bing.com" not in parsed.netloc:
        return url
    value = parse_qs(parsed.query).get("u", [""])[0]
    if not value:
        return url
    if value.startswith("a1"):
        value = value[2:]
    try:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode((value + padding).encode("utf-8")).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return unquote(value)


def extract_page_evidence(html: str, max_length: int = 520) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    page_title = clean_text(soup.title.string if soup.title else "", 120)
    meta = soup.find("meta", attrs={"name": "description"})
    meta_text = clean_text(meta.get("content") if meta else "", 220)
    body_text = clean_text(soup.get_text(" ", strip=True), max_length)
    evidence = " ".join(part for part in [page_title, meta_text, body_text] if part)
    return page_title, clean_text(evidence, max_length)


def matching_terms(text: str, keywords: list[str]) -> list[str]:
    lowered = text.lower()
    return [keyword for keyword in keywords if keyword.lower() in lowered or keyword in text]


def parse_date(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    try:
        parsed = date_parser.parse(value)
        return parsed.date().isoformat()
    except (ValueError, TypeError, OverflowError):
        return fallback


def relevance_score(text: str, keywords: list[str]) -> int:
    lowered = text.lower()
    score = 0
    for keyword in keywords:
        if keyword.lower() in lowered:
            score += 8 if len(keyword) > 2 else 3
    return score


def request_url(ctx: CollectContext, url: str) -> requests.Response | None:
    try:
        response = requests.get(
            url,
            timeout=ctx.timeout,
            headers={"User-Agent": ctx.user_agent, "Accept": "text/html,application/rss+xml,application/xml;q=0.9,*/*;q=0.8"},
        )
        response.raise_for_status()
        return response
    except requests.RequestException as exc:
        ctx.logs.append(f"SKIP {url}: {exc}")
        return None
    finally:
        time.sleep(ctx.delay)


def collect_rss(ctx: CollectContext, today: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    core_keywords = ctx.config.get("keywords", {}).get("hotspot_core", [])
    per_source_limit = int(ctx.config.get("request", {}).get("max_rss_items_per_source", 10))

    for source in ctx.config.get("rss_sources", []):
        response = request_url(ctx, source["url"])
        if response is None:
            continue

        feed = feedparser.parse(response.content)
        if getattr(feed, "bozo", False):
            ctx.logs.append(f"WARN {source['name']}: RSS parse warning, trying available entries.")

        entries = feed.entries[:per_source_limit]
        if not entries:
            ctx.logs.append(f"SKIP {source['name']}: no RSS entries.")
            continue

        accepted = 0
        for entry in entries:
            title = clean_text(getattr(entry, "title", ""))
            summary = clean_text(getattr(entry, "summary", "") or getattr(entry, "description", ""))
            url = getattr(entry, "link", source["url"])
            text = " ".join([title, summary, source.get("category", ""), source.get("name", "")])
            score = relevance_score(text, core_keywords)

            if score <= 0 and accepted >= 2:
                continue

            item = {
                "id": stable_id(source["name"], url, title),
                "kind": "article",
                "title": title or source["name"],
                "summary": summary,
                "source": source["name"],
                "category": source.get("category", "设计趋势"),
                "url": url,
                "publishedDate": parse_date(getattr(entry, "published", None) or getattr(entry, "updated", None), today),
                "score": max(score, 8 if accepted < 2 else 0),
                "keywords": [keyword for keyword in core_keywords if keyword.lower() in text.lower()][:8],
            }
            items.append(item)
            accepted += 1

        ctx.logs.append(f"OK RSS {source['name']}: {accepted} accepted / {len(entries)} read.")

    return items


def collect_company_pages(ctx: CollectContext, today: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    company_statuses: list[dict[str, Any]] = ctx.config.setdefault("_company_statuses", [])
    job_keywords = [
        *ctx.config.get("keywords", {}).get("job_core", []),
        *ctx.config.get("keywords", {}).get("job_industries", []),
    ]
    checked_at = datetime.now().astimezone().isoformat(timespec="seconds")

    for company in ctx.config.get("company_careers", []):
        response = request_url(ctx, company["url"])
        page_title = ""
        snippet = ""
        status = "blocked_or_failed"
        matched: list[str] = []
        message = ""

        if response is not None:
            page_title, snippet = extract_page_evidence(response.text)
            actual_text = " ".join([page_title, snippet])
            text = " ".join([actual_text, " ".join(company.get("keywords", []))])
            matched = matching_terms(actual_text, job_keywords)
            status = "success" if matched else "no_matching_jobs"
            message = "matched job keywords" if matched else "career page reachable, no matching job keywords"
            ctx.logs.append(f"OK COMPANY {company['company']}: {status}, matched {len(matched)} terms.")
        else:
            message = "career page blocked, failed, or timed out"
            ctx.logs.append(f"WARN COMPANY {company['company']}: blocked_or_failed.")

        company_statuses.append(
            {
                "company": company["company"],
                "status": status,
                "sourceUrl": company["url"],
                "checkedAt": checked_at,
                "matchedCount": len(matched),
                "evidenceText": snippet,
                "message": message,
            }
        )

        text = " ".join([page_title, snippet, " ".join(company.get("keywords", []))])
        if status == "blocked_or_failed":
            continue
        items.append(
            {
                "id": stable_id(company["company"], company["url"], today),
                "kind": "job_page",
                "company": company["company"],
                "title": page_title or f"{company['company']} 招聘页",
                "summary": snippet or f"{company['company']} 官方招聘入口，今日未能稳定解析岗位详情。",
                "source": "公司官网招聘页",
                "category": "招聘",
                "url": company["url"],
                "publishedDate": today,
                "city": company["city"],
                "direction": company["direction"],
                "experience": company["experience"],
                "score": relevance_score(text, job_keywords) + 30,
                "keywords": company.get("keywords", []),
                "matchedTerms": matched,
                "sourceType": "official",
                "status": status,
                "crawlStatus": status,
                "evidenceText": snippet,
                "lastCheckedAt": checked_at,
            }
        )

    return items


def fetch_search_detail(ctx: CollectContext, url: str) -> dict[str, Any]:
    response = request_url(ctx, url)
    if response is None:
        return {
            "detailFetched": False,
            "detailTitle": "",
            "evidenceText": "",
            "detailDomain": domain_name(url),
        }
    title, evidence = extract_page_evidence(response.text)
    return {
        "detailFetched": True,
        "detailTitle": title,
        "evidenceText": evidence,
        "detailDomain": domain_name(url),
    }


def collect_bing_group(
    ctx: CollectContext,
    today: str,
    config_key: str,
    kind: str,
    category: str,
    keyword_key: str,
) -> list[dict[str, Any]]:
    search_config = ctx.config.get(config_key, {})
    if not search_config.get("enabled", False):
        return []

    items: list[dict[str, Any]] = []
    queries = search_config.get("queries", [])[: int(ctx.config.get("request", {}).get("max_search_queries_per_run", 6))]
    keywords = [
        *ctx.config.get("keywords", {}).get(keyword_key, []),
        *ctx.config.get("keywords", {}).get("job_industries", []),
    ]

    for query in queries:
        url = f"https://www.bing.com/search?q={quote_plus(query)}"
        response = request_url(ctx, url)
        if response is None:
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        result_nodes = soup.select("li.b_algo")[:1]
        accepted = 0

        for node in result_nodes:
            link = node.find("a", href=True)
            if not link:
                continue
            title = clean_text(link.get_text(" ", strip=True))
            snippet = clean_text(node.get_text(" ", strip=True), 300)
            result_url = unwrap_bing_url(link["href"])
            if "bing.com" in domain_name(result_url):
                continue
            text = f"{query} {title} {snippet}"
            detail = fetch_search_detail(ctx, result_url)
            detail_text = f"{text} {detail.get('detailTitle', '')} {detail.get('evidenceText', '')}"
            items.append(
                {
                    "id": stable_id(query, result_url, title),
                    "kind": kind,
                    "title": detail.get("detailTitle") or title or query,
                    "summary": detail.get("evidenceText") or snippet,
                    "source": detail.get("detailDomain") or "Bing Search",
                    "category": category,
                    "url": result_url,
                    "publishedDate": today,
                    "query": query,
                    "score": relevance_score(detail_text, keywords) + 16,
                    "keywords": [query, *[keyword for keyword in keywords if keyword in detail_text][:8]],
                    "sourceType": "search_result",
                    **detail,
                }
            )
            accepted += 1

        ctx.logs.append(f"OK SEARCH {query}: {accepted} results accepted.")

    return items


def collect_bing_results(ctx: CollectContext, today: str) -> list[dict[str, Any]]:
    return [
        *collect_bing_group(ctx, today, "job_search_queries", "job_search_result", "招聘搜索", "job_core"),
        *collect_bing_group(ctx, today, "hotspot_search_queries", "hotspot_search_result", "设计热点搜索", "hotspot_core"),
    ]


def collect_sources(config_path: Path = DEFAULT_CONFIG, today: str | None = None) -> dict[str, Any]:
    today = today or datetime.now().date().isoformat()
    config = load_config(config_path)
    ctx = CollectContext(config=config, logs=[])

    items: list[dict[str, Any]] = []
    items.extend(collect_rss(ctx, today))
    items.extend(collect_company_pages(ctx, today))
    items.extend(collect_bing_results(ctx, today))

    source_names = sorted({item.get("source", "未知来源") for item in items})
    failed_count = len([log for log in ctx.logs if log.startswith("SKIP") or log.startswith("WARN")])
    status = "success"
    if not items:
        status = "fallback"
    elif failed_count:
        status = "partial"

    return {
        "date": today,
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "sourceCount": len(source_names),
        "items": items,
        "logs": ctx.logs,
        "companyCrawlStatus": config.get("_company_statuses", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect public industrial design sources.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--date", default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    result = collect_sources(args.config, args.date)
    output = args.output or COLLECTED_DIR / f"{result['date']}-sources.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Collected {len(result['items'])} source items from {result['sourceCount']} sources.")
    print(f"Collection status: {result['status']}")
    print(f"Wrote {output.relative_to(ROOT)}")
    for log in result["logs"]:
        print(log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
