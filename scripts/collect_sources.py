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
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse

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


def extract_page_evidence(html: str, max_length: int = 3200) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    page_title = clean_text(soup.title.string if soup.title else "", 120)
    meta = soup.find("meta", attrs={"name": "description"})
    meta_text = clean_text(meta.get("content") if meta else "", 220)
    body_text = clean_text(soup.get_text(" ", strip=True), max_length)
    evidence = " ".join(part for part in [page_title, meta_text, body_text] if part)
    return page_title, clean_text(evidence, max_length)


def extract_between(text: str, start_labels: list[str], end_labels: list[str], max_length: int = 700) -> str:
    for label in start_labels:
        start = text.find(label)
        if start == -1:
            continue
        start += len(label)
        end_positions = [text.find(end_label, start) for end_label in end_labels]
        end_positions = [position for position in end_positions if position != -1]
        end = min(end_positions) if end_positions else min(len(text), start + max_length)
        value = clean_text(text[start:end], max_length)
        value = re.sub(r"^[：:\\s]+", "", value).strip()
        if value and value not in {"无", "暂无", "申请职位"}:
            return value
    return ""


def extract_job_detail_fields(title: str, evidence: str) -> dict[str, str]:
    text = clean_text(f"{title} {evidence}", 4000)
    job_title = extract_between(text, ["职位名称：", "职位名称:", "岗位名称：", "岗位名称:"], ["工作地点", "职位类别", "招聘渠道", "工作职责", "岗位职责"], 120)
    if not job_title:
        title_parts = [clean_text(part, 80) for part in re.split(r"[-|｜]", title)]
        design_parts = [
            part
            for part in title_parts
            if any(token in part for token in ["工业设计", "产品设计", "ID", "CMF", "硬件产品设计", "消费电子", "智能硬件", "家电", "机器人", "清洁电器"])
            and part not in {"设计师", "职位详情", "小米"}
        ]
        if design_parts:
            job_title = max(design_parts, key=len)
        else:
            match = re.search(r"(工业设计师|产品设计师|ID设计师|CMF设计师|硬件产品设计师|消费电子产品设计师|智能硬件工业设计师|家电工业设计师|机器人产品设计师|清洁电器工业设计师)", text)
            job_title = clean_text(match.group(1), 80) if match else ""
    work_city = extract_between(text, ["工作地点：", "工作地点:", "工作城市：", "工作城市:", "地点：", "地点:"], ["职位类别", "招聘渠道", "工作职责", "岗位职责", "任职要求", "工作要求"], 80)
    job_category = extract_between(text, ["职位类别：", "职位类别:", "岗位类别：", "岗位类别:"], ["职位名称", "招聘渠道", "工作职责", "岗位职责", "职位描述", "任职要求", "工作要求"], 100)
    if "设计师" in job_category:
        job_category = "设计师"
    responsibilities = extract_between(
        text,
        ["工作职责：", "工作职责:", "岗位职责：", "岗位职责:", "职位描述：", "职位描述:"],
        ["工作要求", "任职要求", "职位要求", "申请职位", "投递", "预约维修服务", "帮助中心"],
        900,
    )
    requirements = extract_between(
        text,
        ["工作要求：", "工作要求:", "任职要求：", "任职要求:", "职位要求：", "职位要求:"],
        ["申请职位", "投递", "预约维修服务", "帮助中心", "相关下载", "关于"],
        700,
    )
    if len(requirements) < 8 or requirements in {"申请职位", "投递"}:
        requirements = ""
    return {
        "jobTitle": job_title,
        "workCity": work_city,
        "jobCategory": job_category,
        "responsibilitiesSummary": responsibilities,
        "requirementsSummary": requirements,
    }


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
        if response.apparent_encoding and response.encoding and response.encoding.lower() in {"iso-8859-1", "windows-1252"}:
            response.encoding = response.apparent_encoding
        return response
    except requests.RequestException as exc:
        ctx.logs.append(f"SKIP {url}: {exc}")
        return None
    finally:
        time.sleep(ctx.delay)


def configured_job_keywords(ctx: CollectContext) -> list[str]:
    keywords = ctx.config.get("keywords", {})
    return [
        *keywords.get("job_titles", []),
        *keywords.get("job_core", []),
        "工业设计",
        "产品设计",
        "ID",
        "UX",
        "CMF",
        "外观设计",
        "设计类",
        "Industrial Designer",
        "Product Designer",
    ]


def configured_experience_keywords(ctx: CollectContext) -> list[str]:
    keywords = ctx.config.get("keywords", {})
    return keywords.get("experience", [])


def configured_city_keywords(ctx: CollectContext) -> list[str]:
    keywords = ctx.config.get("keywords", {})
    return [
        *ctx.config.get("city_priority", {}).get("first", []),
        *ctx.config.get("city_priority", {}).get("second", []),
        *keywords.get("city_first", []),
        *keywords.get("city_second", []),
        "北京",
        "Peking",
        "Shanghai",
        "Shenzhen",
        "Guangzhou",
        "Suzhou",
        "Hangzhou",
        "Dongguan",
        "Nanjing",
    ]


def company_aliases(company: dict[str, Any]) -> list[str]:
    aliases = [company["company"], company["company"].split(" ")[0], *company.get("aliases", [])]
    if "DJI" in company["company"]:
        aliases.extend(["DJI", "大疆"])
    if "Insta360" in company["company"]:
        aliases.extend(["Insta360", "影石"])
    if "Anker" in company["company"]:
        aliases.extend(["Anker", "安克"])
    if "Baseus" in company["company"]:
        aliases.extend(["Baseus", "倍思"])
    return sorted({alias for alias in aliases if alias})


def city_aliases(city: str) -> list[str]:
    mapping = {
        "北京": ["北京", "Peking", "Beijing"],
        "上海": ["上海", "Shanghai"],
        "深圳": ["深圳", "Shenzhen"],
        "广州": ["广州", "Guangzhou"],
        "苏州": ["苏州", "Suzhou"],
        "杭州": ["杭州", "Hangzhou"],
        "东莞": ["东莞", "Dongguan"],
        "南京": ["南京", "Nanjing"],
        "佛山": ["佛山", "Foshan"],
        "青岛": ["青岛", "Qingdao"],
    }
    return mapping.get(city, [city])


def normalize_city(value: str, fallback: str) -> str:
    mapping = {
        "Peking": "北京",
        "Beijing": "北京",
        "Shanghai": "上海",
        "Shenzhen": "深圳",
        "Guangzhou": "广州",
        "Suzhou": "苏州",
        "Hangzhou": "杭州",
        "Dongguan": "东莞",
        "Nanjing": "南京",
        "Foshan": "佛山",
        "Qingdao": "青岛",
    }
    if not value:
        return fallback
    if value in mapping:
        return mapping[value]
    for raw, normalized in mapping.items():
        if raw in value:
            return normalized
    for city in ["北京", "上海", "深圳", "广州", "苏州", "杭州", "东莞", "南京", "佛山", "青岛"]:
        if city in value:
            return city
    return value or fallback


def source_type_from_url(ctx: CollectContext, url: str, fallback: str = "search_result") -> str:
    domain = domain_name(url)
    official_domains = [domain_name(company.get("url", "")) for company in ctx.config.get("company_careers", [])]
    official_domains.extend(["hr.xiaomi.com", "career.huawei.com", "careers.dji.com", "careers.narwal.com", "careers.midea.com", "campus.tcl.com", "maker.haier.net"])
    job_board_domains = ["nowcoder.com", "shixiseng.com", "liepin.com", "lagou.com", "linkedin.com", "zhipin.com", "51job.com", "zhaopin.com"]
    if any(item and (domain == item or domain.endswith(f".{item}")) for item in official_domains):
        return "official"
    if any(item in domain for item in job_board_domains):
        return "job_board"
    return fallback


def infer_company_from_config(ctx: CollectContext, text: str) -> dict[str, Any] | None:
    for company in ctx.config.get("company_careers", []):
        if any(alias and alias.lower() in text.lower() for alias in company_aliases(company)):
            return company
    return None


def infer_city_from_text(ctx: CollectContext, text: str, fallback: str = "全国") -> str:
    for city in configured_city_keywords(ctx):
        if city and city in text:
            return normalize_city(city, fallback)
    return fallback


def verify_job_detail_content(
    ctx: CollectContext,
    url: str,
    title: str,
    evidence: str,
    expected_company: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = " ".join([title, evidence])
    fields = extract_job_detail_fields(title, evidence)
    company = expected_company or infer_company_from_config(ctx, text)
    source_type = source_type_from_url(ctx, url)
    aliases = company_aliases(company) if company else []
    expected_city = company.get("city", "全国") if company else "全国"
    company_ok = bool(company and any(alias and alias.lower() in text.lower() for alias in aliases))
    job_terms = matching_terms(text, configured_job_keywords(ctx))
    city_terms = matching_terms(" ".join([fields.get("workCity", ""), text]), [*city_aliases(expected_city), *configured_city_keywords(ctx)])
    city = normalize_city(fields.get("workCity") or (city_terms[0] if city_terms else ""), expected_city)
    has_location = bool(city_terms)
    has_detail_title = bool(fields.get("jobTitle")) and not any(token in fields["jobTitle"] for token in ["社会招聘", "校园招聘", "职位搜索"])
    has_role_detail = bool(fields.get("responsibilitiesSummary") or fields.get("requirementsSummary"))
    strong_role_text = " ".join([fields.get("jobTitle", ""), fields.get("responsibilitiesSummary", ""), fields.get("requirementsSummary", ""), evidence])
    has_strong_design_signal = bool(matching_terms(strong_role_text, configured_job_keywords(ctx)))
    generic_listing = (
        any(token in title for token in ["社会招聘", "校园招聘", "职位列表", "岗位投递"])
        and any(token in evidence for token in ["职位名称", "关键字搜索", "职位筛选", "全部职位", "职位分类"])
        and not any(token in evidence for token in ["职位详情", "岗位职责", "职位描述", "任职要求", "工作职责"])
    )
    status = "unverified"
    confidence = 58

    if company_ok and job_terms and has_location and has_detail_title and not generic_listing:
        if source_type == "official":
            if has_role_detail and has_strong_design_signal:
                status = "verified"
                confidence = 95
            else:
                status = "likely"
                confidence = 78
        elif source_type == "job_board":
            status = "likely" if has_role_detail and has_strong_design_signal else "unverified"
            confidence = 84 if status == "likely" else 62
        else:
            status = "unverified"
            confidence = 65

    return {
        "detailFetched": True,
        "detailTitle": title,
        "evidenceText": evidence,
        "detailDomain": domain_name(url),
        "verificationStatus": status,
        "confidenceScore": confidence,
        "sourceType": source_type,
        "company": company.get("company") if company else "",
        "city": city,
        **fields,
        "matchedTerms": [*job_terms[:8], *city_terms[:4]],
    }


def verify_job_detail_page(
    ctx: CollectContext,
    url: str,
    expected_company: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = request_url(ctx, url)
    if response is None:
        detail = {
            "detailFetched": False,
            "detailTitle": "",
            "evidenceText": "",
            "detailDomain": domain_name(url),
            "verificationStatus": "unverified",
            "confidenceScore": 45,
            "sourceType": source_type_from_url(ctx, url),
            "company": expected_company.get("company", "") if expected_company else "",
            "city": expected_company.get("city", "全国") if expected_company else "全国",
            "matchedTerms": [],
        }
        ctx.config.setdefault("_job_detail_checks", []).append(
            {"url": url, "status": "failed", "passed": False, "downgraded": False}
        )
        return detail
    title, evidence = extract_page_evidence(response.text)
    detail = verify_job_detail_content(ctx, url, title, evidence, expected_company)
    ctx.config.setdefault("_job_detail_checks", []).append(
        {
            "url": url,
            "status": detail.get("verificationStatus"),
            "passed": detail.get("verificationStatus") in {"verified", "likely"},
            "downgraded": detail.get("sourceType") == "official" and detail.get("verificationStatus") != "verified",
        }
    )
    return detail


def discover_job_detail_links(base_url: str, html: str, limit: int) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for link in soup.find_all("a", href=True):
        href = urljoin(base_url, link["href"])
        label = clean_text(link.get_text(" ", strip=True), 80)
        lowered = f"{href} {label}".lower()
        looks_like_detail = any(token in lowered for token in ["detail", "job/view", "jobadid", "position/detail", "positionid=", "postid=", "jobid="])
        looks_like_generic_channel = any(href.rstrip("/").endswith(token) for token in ["/social", "/campus", "/school", "/jobs", "/careers", "/recruit"])
        if looks_like_detail and not looks_like_generic_channel:
            links.append(href)
    return list(dict.fromkeys(links))[:limit]


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
    job_keywords = [*configured_job_keywords(ctx), *ctx.config.get("keywords", {}).get("job_industries", [])]
    max_detail_links = int(ctx.config.get("request", {}).get("max_company_detail_links", 6))
    checked_at = datetime.now().astimezone().isoformat(timespec="seconds")

    for company in ctx.config.get("company_careers", []):
        response = request_url(ctx, company["url"])
        page_title = ""
        snippet = ""
        status = "blocked_or_failed"
        matched: list[str] = []
        message = ""
        detail_urls = list(dict.fromkeys(company.get("detail_urls", [])))
        verified_items: list[dict[str, Any]] = []

        if response is not None:
            page_title, snippet = extract_page_evidence(response.text)
            detail_urls.extend(discover_job_detail_links(response.url, response.text, max_detail_links))
            detail_urls = list(dict.fromkeys(detail_urls))[:max_detail_links]
            for detail_url in detail_urls:
                detail = verify_job_detail_page(ctx, detail_url, company)
                if detail.get("verificationStatus") not in {"verified", "likely"}:
                    continue
                verified_items.append(
                    {
                        "id": stable_id(company["company"], detail_url, today),
                        "kind": "job_page",
                        "company": company["company"],
                        "title": detail.get("detailTitle") or f"{company['company']} 招聘岗位",
                        "summary": detail.get("evidenceText") or f"{company['company']} 官方招聘详情页。",
                        "source": "公司官网招聘页",
                        "category": "招聘",
                        "url": detail_url,
                        "publishedDate": today,
                        "city": detail.get("city") or company["city"],
                        "jobTitle": detail.get("jobTitle", ""),
                        "jobCategory": detail.get("jobCategory", ""),
                        "responsibilitiesSummary": detail.get("responsibilitiesSummary", ""),
                        "requirementsSummary": detail.get("requirementsSummary", ""),
                        "direction": company["direction"],
                        "experience": company["experience"],
                        "score": relevance_score(" ".join([detail.get("detailTitle", ""), detail.get("evidenceText", "")]), job_keywords) + 45,
                        "keywords": [*company.get("keywords", []), *detail.get("matchedTerms", [])],
                        "matchedTerms": detail.get("matchedTerms", []),
                        "sourceType": detail.get("sourceType", "official"),
                        "status": "success",
                        "crawlStatus": "success",
                        "detailFetched": True,
                        "detailTitle": detail.get("detailTitle", ""),
                        "evidenceText": detail.get("evidenceText", ""),
                        "lastCheckedAt": checked_at,
                        "verificationStatus": detail.get("verificationStatus"),
                        "confidenceScore": detail.get("confidenceScore"),
                    }
                )
            actual_text = " ".join([page_title, snippet])
            text = " ".join([actual_text, " ".join(company.get("keywords", []))])
            matched = matching_terms(actual_text, job_keywords)
            if verified_items:
                status = "success"
                message = f"verified {len(verified_items)} public job detail page(s)"
            else:
                status = "no_matching_jobs"
                message = "career page reachable, no verified public job detail"
            ctx.logs.append(f"OK COMPANY {company['company']}: {status}, matched {len(matched)} terms, details {len(verified_items)}.")
        else:
            message = "career page blocked, failed, or timed out"
            ctx.logs.append(f"WARN COMPANY {company['company']}: blocked_or_failed.")

        company_statuses.append(
            {
                "company": company["company"],
                "status": status,
                "sourceUrl": company["url"],
                "checkedAt": checked_at,
                "matchedCount": len(verified_items),
                "evidenceText": snippet,
                "message": message,
            }
        )

        items.extend(verified_items)

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
    return verify_job_detail_content(ctx, url, title, evidence)


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
    per_query_limit = int(ctx.config.get("request", {}).get("max_search_results_per_query", 1))
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
        result_nodes = soup.select("li.b_algo")[:per_query_limit]
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
            source_type = detail.get("sourceType") or source_type_from_url(ctx, result_url)
            inferred_company = detail.get("company") or ""
            inferred_city = detail.get("city") or infer_city_from_text(ctx, detail_text)
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
                    "sourceType": source_type,
                    "company": inferred_company,
                    "city": inferred_city,
                    "verificationStatus": detail.get("verificationStatus", "unverified"),
                    "confidenceScore": detail.get("confidenceScore", 58),
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
        "jobDetailChecks": config.get("_job_detail_checks", []),
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
