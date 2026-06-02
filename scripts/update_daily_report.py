#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from collect_sources import collect_sources
from summarize_report import build_daily_report, dedupe_jobs, is_high_match_job, stable_id, to_legacy_news, to_legacy_trend

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PUBLIC_DATA_DIR = ROOT / "public" / "data"
REPORT_KEYS = ["jobOpportunities", "designHotspots", "companyUpdates", "actions"]


def read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def report_index_item(report: dict[str, Any]) -> dict[str, Any]:
    jobs = report.get("jobOpportunities", report.get("jobs", []))
    hotspots = report.get("designHotspots", report.get("trends", []))
    high_match = [job for job in report.get("highMatchJobs", jobs) if is_high_match_job(job)]
    return {
        "date": report["date"],
        "title": report["title"],
        "summary": report["summary"],
        "newsCount": len(hotspots),
        "jobsCount": len(jobs),
        "trendsCount": len(hotspots),
        "highMatchJobsCount": len(high_match),
    }


def list_existing_reports(data_dir: Path) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    reports_dir = data_dir / "reports"
    if not reports_dir.exists():
        return reports
    for path in sorted(reports_dir.glob("*.json")):
        data = read_json(path)
        if isinstance(data, dict) and data.get("date"):
            reports.append(data)
    return reports


def sync_to_public() -> None:
    PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    reports_dir = PUBLIC_DATA_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    for old in reports_dir.glob("*.json"):
        old.unlink()

    for path in DATA_DIR.glob("*.json"):
        shutil.copy2(path, PUBLIC_DATA_DIR / path.name)
    for path in (DATA_DIR / "reports").glob("*.json"):
        shutil.copy2(path, reports_dir / path.name)


def legacy_news_to_hotspot(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id", ""),
        "title": item.get("title", ""),
        "summary": item.get("summary", ""),
        "source": item.get("source", "历史数据"),
        "category": item.get("category", "工业设计趋势"),
        "url": item.get("url", "https://github.com/iron2002-xtc/industrial-design-intelligence-mvp"),
        "date": item.get("date", ""),
        "importanceScore": item.get("importanceScore", 76),
        "sourceQualityScore": 60,
        "relevanceScore": item.get("importanceScore", 76),
        "designInsight": item.get("designInsight", "可作为作品集调研素材继续核对。"),
        "relatedCompanies": [],
        "tags": item.get("keywords", []),
    }


def legacy_trend_to_hotspot(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id", ""),
        "title": item.get("title", ""),
        "summary": item.get("trendSummary", ""),
        "source": (item.get("relatedCases") or ["历史趋势"])[0],
        "category": item.get("category", "工业设计趋势"),
        "url": item.get("url", "https://github.com/iron2002-xtc/industrial-design-intelligence-mvp"),
        "date": item.get("date", ""),
        "importanceScore": 76,
        "sourceQualityScore": 60,
        "relevanceScore": 76,
        "designInsight": item.get("designInspiration", "可作为作品集调研素材继续核对。"),
        "relatedCompanies": item.get("relatedCases", []),
        "tags": item.get("keywords", []),
    }


def ensure_job_fields(job: dict[str, Any]) -> dict[str, Any]:
    job.setdefault("jobType", "可跟进")
    job.setdefault("sourceQualityScore", 70)
    job.setdefault("relevanceScore", job.get("matchScore", 70))
    if job.get("verificationStatus") not in {"verified", "likely", "unverified", "fallback"}:
        job["verificationStatus"] = "fallback" if job.get("sourceType") == "fallback" else "unverified"
    if job.get("sourceType") not in {"official", "job_board", "search_result", "media", "fallback"}:
        job["sourceType"] = "fallback" if job["verificationStatus"] == "fallback" else "search_result"
    job.setdefault("applyUrl", job.get("url", "") if job["verificationStatus"] in {"verified", "likely"} else "")
    job.setdefault("originalUrl", job.get("url", ""))
    job.setdefault("evidenceText", job.get("requirementsSummary", "历史数据缺少校验片段，请打开原始链接核对。"))
    job.setdefault("lastCheckedAt", job.get("date", ""))
    if "confidenceScore" not in job:
        job["confidenceScore"] = {"verified": 92, "likely": 82, "unverified": 55, "fallback": 45}[job["verificationStatus"]]
    if job["verificationStatus"] == "fallback":
        job["sourceType"] = "fallback"
        job["confidenceScore"] = min(job.get("confidenceScore", 45), 50)
        job["matchScore"] = min(job.get("matchScore", 65), 65)
    if job["verificationStatus"] == "unverified":
        job["confidenceScore"] = min(job.get("confidenceScore", 55), 70)
        job["matchScore"] = min(job.get("matchScore", 80), 80)
    if job["sourceType"] == "search_result":
        job["matchScore"] = min(job.get("matchScore", 80), 80)
    job.setdefault("requirementsSummary", "请打开原始链接核对岗位职责、经验要求和作品集要求。")
    job.setdefault("tags", job.get("keywords", []))
    job.setdefault("keywords", job.get("tags", []))
    return job


def default_company_updates(report: dict[str, Any]) -> list[dict[str, Any]]:
    updates = []
    for job in report.get("highMatchJobs", [])[:6]:
        updates.append(
            {
                "id": stable_id(report["date"], "company", job["company"]),
                "company": job["company"],
                "title": f"{job['company']}：{job['direction']}岗位入口值得核对",
                "summary": f"{job['city']} / {job.get('jobType', '可跟进')} / 匹配度 {job['matchScore']}，建议查看原始招聘链接确认岗位是否开放。",
                "category": "招聘",
                "url": job["url"],
                "date": report["date"],
                "relevanceScore": job["matchScore"],
                "designRelation": f"与{job['direction']}、作品集项目选择和求职投递优先级直接相关。",
                "tags": [job["direction"], job.get("jobType", "可跟进")],
            }
        )
    return updates


def ensure_actions(report: dict[str, Any]) -> list[dict[str, Any]]:
    actions = [
        action
        for action in report.get("actions", [])
        if "小红书"
        not in f"{action.get('title', '')} {action.get('description', '')} {' '.join(action.get('keywords', []))}"
    ]
    if actions:
        return actions[:4]
    jobs = report.get("highMatchJobs") or report.get("jobOpportunities", [])
    hotspots = report.get("designHotspots", [])
    if not jobs or not hotspots:
        return []
    return [
        {
            "id": stable_id(report["date"], "action", "job"),
            "title": "今日建议重点关注的岗位",
            "description": f"优先核对 {jobs[0]['company']} 的原始招聘链接，确认是否适合应届/初级投递。",
            "priority": "high",
            "keywords": ["求职", jobs[0]["company"], jobs[0]["direction"]],
        },
        {
            "id": stable_id(report["date"], "action", "hotspot"),
            "title": "今日建议收藏的设计热点",
            "description": f"收藏“{hotspots[0]['title']}”，补充到作品集调研或竞品矩阵。",
            "priority": "medium",
            "keywords": ["设计热点", hotspots[0]["category"]],
        },
    ]


def has_removed_topic(item: dict[str, Any]) -> bool:
    text = json.dumps(item, ensure_ascii=False)
    return "小红书" in text or "社交媒体" in text or "运营建议" in text


def ensure_report_metadata(report: dict[str, Any]) -> dict[str, Any]:
    report.setdefault("dataMode", "Mock")
    report.setdefault("collectionStatus", "success")
    report.setdefault("statusMessage", "")
    report.setdefault("qualitySummary", report.get("summary", ""))
    jobs = dedupe_jobs([ensure_job_fields(job) for job in report.get("jobOpportunities", report.get("jobs", []))])
    report["jobOpportunities"] = sorted(jobs, key=lambda item: item.get("matchScore", 0), reverse=True)
    report["highMatchJobs"] = sorted(
        [job for job in report["jobOpportunities"] if is_high_match_job(job)],
        key=lambda item: item.get("matchScore", 0),
        reverse=True,
    )
    if "designHotspots" not in report:
        report["designHotspots"] = [
            *[legacy_news_to_hotspot(item) for item in report.get("topNews", [])],
            *[legacy_trend_to_hotspot(item) for item in report.get("trends", [])],
        ]
    report["designHotspots"] = [hotspot for hotspot in report["designHotspots"] if not has_removed_topic(hotspot)]
    for hotspot in report["designHotspots"]:
        hotspot.setdefault("sourceQualityScore", 60)
        hotspot.setdefault("relevanceScore", hotspot.get("importanceScore", 70))
        hotspot.setdefault("confidenceScore", hotspot.get("sourceQualityScore", 60))
        hotspot.setdefault("designRelevanceReason", hotspot.get("designInsight", "历史数据缺少设计相关性说明。"))
        hotspot.setdefault("productCategory", hotspot.get("category", "工业设计趋势"))
        hotspot.setdefault("relatedBrand", "、".join(hotspot.get("relatedCompanies", [])))
        hotspot.setdefault("isGenericSearchResult", False)
        hotspot.setdefault("evidenceText", hotspot.get("summary", "历史数据缺少原始证据片段。"))
        hotspot.setdefault("relatedCompanies", [])
        hotspot.setdefault("tags", hotspot.get("keywords", []))
    report["companyUpdates"] = report.get("companyUpdates") or default_company_updates(report)
    report["companyUpdates"] = [item for item in report["companyUpdates"] if not has_removed_topic(item)]
    report["actions"] = ensure_actions(report)
    report["jobs"] = report["jobOpportunities"]
    report["topNews"] = [to_legacy_news(item) for item in report["designHotspots"][:5]]
    report["trends"] = [to_legacy_trend(item) for item in report["designHotspots"]]
    report.setdefault("aiTools", [])
    report.setdefault("hardwareObservation", [to_legacy_news(item) for item in report["designHotspots"] if item["category"] in {"智能硬件", "AI硬件", "机器人", "清洁电器"}][:3])
    quality_report = report.get("qualityReport") if isinstance(report.get("qualityReport"), dict) else {}
    quality_report.setdefault("totalCollected", 0)
    quality_report.setdefault("afterDedup", 0)
    quality_report.setdefault("afterQualityFilter", len(report["jobOpportunities"]) + len(report["designHotspots"]))
    quality_report.update(
        {
        "verifiedJobsCount": len([job for job in report["jobOpportunities"] if job.get("verificationStatus") == "verified"]),
        "likelyJobsCount": len([job for job in report["jobOpportunities"] if job.get("verificationStatus") == "likely"]),
        "unverifiedJobsCount": len([job for job in report["jobOpportunities"] if job.get("verificationStatus") == "unverified"]),
        "fallbackJobsCount": len([job for job in report["jobOpportunities"] if job.get("verificationStatus") == "fallback"]),
        "officialSourceJobsCount": len([job for job in report["jobOpportunities"] if job.get("sourceType") == "official"]),
        "jobBoardJobsCount": len([job for job in report["jobOpportunities"] if job.get("sourceType") == "job_board"]),
        "searchResultJobsCount": len([job for job in report["jobOpportunities"] if job.get("sourceType") == "search_result"]),
        "highMatchVerifiedJobsCount": len([job for job in report["jobOpportunities"] if is_high_match_job(job)]),
        }
    )
    quality_report.setdefault("genericSearchResultsFiltered", 0)
    quality_report.setdefault("failedSources", [])
    quality_report.setdefault("companyCrawlStatus", [])
    report["qualityReport"] = quality_report
    report["totalItems"] = sum(len(report.get(key, [])) for key in REPORT_KEYS)
    return report


def update_daily_report(date: str | None = None) -> dict[str, Any]:
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    report_date = date or now.date().isoformat()
    generated_at = now.isoformat(timespec="seconds")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "reports").mkdir(parents=True, exist_ok=True)

    previous_latest = read_json(DATA_DIR / "latest.json")
    collected = collect_sources(today=report_date)
    collected_dir = DATA_DIR / "collected"
    write_json(collected_dir / f"{report_date}-sources.json", collected)

    report = build_daily_report(
        collected=collected,
        date=report_date,
        generated_at=generated_at,
        previous_report=previous_latest if isinstance(previous_latest, dict) else None,
    )
    report = ensure_report_metadata(report)

    existing_reports = {
        item["date"]: ensure_report_metadata(item)
        for item in list_existing_reports(DATA_DIR)
        if isinstance(item, dict) and item.get("date")
    }
    existing_reports[report_date] = report
    reports = sorted(existing_reports.values(), key=lambda item: item["date"], reverse=True)[:14]
    latest = reports[0]
    index = [report_index_item(item) for item in reports]

    write_json(DATA_DIR / "latest.json", latest)
    write_json(DATA_DIR / "reportsIndex.json", index)

    reports_dir = DATA_DIR / "reports"
    for old in reports_dir.glob("*.json"):
        if old.stem not in {item["date"] for item in reports}:
            old.unlink()
    for item in reports:
        write_json(reports_dir / f"{item['date']}.json", item)

    sync_to_public()

    print(f"Updated daily report: {latest['date']}")
    print(f"Data mode: {latest.get('dataMode', 'Mock')}")
    print(f"Collection status: {latest.get('collectionStatus', 'success')}")
    print(f"Source count: {latest.get('sourceCount', 0)}")
    print(f"Total items: {latest.get('totalItems', 0)}")
    quality = latest.get("qualityReport", {})
    if quality:
        print("Quality report:")
        print(f"- total collected: {quality.get('totalCollected', 0)}")
        print(f"- after dedup: {quality.get('afterDedup', 0)}")
        print(f"- after quality filter: {quality.get('afterQualityFilter', 0)}")
        print(f"- verified jobs: {quality.get('verifiedJobsCount', 0)}")
        print(f"- likely jobs: {quality.get('likelyJobsCount', 0)}")
        print(f"- unverified jobs: {quality.get('unverifiedJobsCount', 0)}")
        print(f"- fallback jobs: {quality.get('fallbackJobsCount', 0)}")
        print(f"- official source jobs: {quality.get('officialSourceJobsCount', 0)}")
        print(f"- job board jobs: {quality.get('jobBoardJobsCount', 0)}")
        print(f"- search result jobs: {quality.get('searchResultJobsCount', 0)}")
        print(f"- high match verified jobs: {quality.get('highMatchVerifiedJobsCount', 0)}")
        print(f"- generic search results filtered: {quality.get('genericSearchResultsFiltered', 0)}")
        failed_sources = quality.get("failedSources", [])
        print(f"- failed sources: {len(failed_sources)}")
        for failed_source in failed_sources[:12]:
            print(f"  - {failed_source}")
        print("- company crawl status:")
        for item in quality.get("companyCrawlStatus", []):
            print(f"  - {item.get('company')}: {item.get('status')} ({item.get('matchedCount', 0)} matches)")
    if latest.get("statusMessage"):
        print(latest["statusMessage"])
    return latest


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect sources and update public DailyReport JSON.")
    parser.add_argument("--date", default=None, help="Override report date, YYYY-MM-DD.")
    args = parser.parse_args()
    update_daily_report(args.date)
    return 0


if __name__ == "__main__":
    sys.exit(main())
