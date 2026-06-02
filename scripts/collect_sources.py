#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

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
    core_keywords = ctx.config.get("keywords", {}).get("core", [])
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
    job_keywords = ctx.config.get("keywords", {}).get("jobs", [])

    for company in ctx.config.get("company_careers", []):
        response = request_url(ctx, company["url"])
        page_title = ""
        snippet = ""
        status = "fallback"

        if response is not None:
            soup = BeautifulSoup(response.text, "html.parser")
            page_title = clean_text(soup.title.string if soup.title else "")
            meta = soup.find("meta", attrs={"name": "description"})
            snippet = clean_text(meta.get("content") if meta else soup.get_text(" ", strip=True), 420)
            status = "checked"
            ctx.logs.append(f"OK JOB {company['company']}: career page checked.")
        else:
            ctx.logs.append(f"WARN JOB {company['company']}: using configured career URL only.")

        text = " ".join([page_title, snippet, " ".join(company.get("keywords", []))])
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
                "status": status,
            }
        )

    return items


def collect_bing_results(ctx: CollectContext, today: str) -> list[dict[str, Any]]:
    search_config = ctx.config.get("search_queries", {})
    if not search_config.get("enabled", False):
        return []

    items: list[dict[str, Any]] = []
    queries = search_config.get("queries", [])[: int(ctx.config.get("request", {}).get("max_search_queries_per_run", 6))]
    job_keywords = ctx.config.get("keywords", {}).get("jobs", [])

    for query in queries:
        url = f"https://www.bing.com/search?q={quote_plus(query)}"
        response = request_url(ctx, url)
        if response is None:
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        result_nodes = soup.select("li.b_algo")[:2]
        accepted = 0

        for node in result_nodes:
            link = node.find("a", href=True)
            if not link:
                continue
            title = clean_text(link.get_text(" ", strip=True))
            snippet = clean_text(node.get_text(" ", strip=True), 300)
            result_url = link["href"]
            text = f"{query} {title} {snippet}"
            items.append(
                {
                    "id": stable_id(query, result_url, title),
                    "kind": "search_result",
                    "title": title or query,
                    "summary": snippet,
                    "source": "Bing Search",
                    "category": "招聘搜索",
                    "url": result_url,
                    "publishedDate": today,
                    "query": query,
                    "score": relevance_score(text, job_keywords) + 16,
                    "keywords": [query, *[keyword for keyword in job_keywords if keyword in text][:6]],
                }
            )
            accepted += 1

        ctx.logs.append(f"OK SEARCH {query}: {accepted} results accepted.")

    return items


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
