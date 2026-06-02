#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PUBLIC_DATA_DIR = ROOT / "public" / "data"
REQUIRED_REPORT_KEYS = [
    "date",
    "title",
    "summary",
    "generatedAt",
    "sourceCount",
    "totalItems",
    "dataMode",
    "qualitySummary",
    "qualityReport",
    "jobOpportunities",
    "highMatchJobs",
    "designHotspots",
    "companyUpdates",
    "actions",
]
REQUIRED_INDEX_KEYS = [
    "date",
    "title",
    "summary",
    "newsCount",
    "jobsCount",
    "trendsCount",
    "highMatchJobsCount",
]
REQUIRED_JOB_KEYS = [
    "verificationStatus",
    "sourceType",
    "applyUrl",
    "originalUrl",
    "evidenceText",
    "lastCheckedAt",
    "confidenceScore",
]
REQUIRED_HOTSPOT_KEYS = [
    "designRelevanceReason",
    "productCategory",
    "relatedBrand",
    "isGenericSearchResult",
    "evidenceText",
    "confidenceScore",
]
REQUIRED_QUALITY_KEYS = [
    "totalCollected",
    "afterDedup",
    "afterQualityFilter",
    "verifiedJobsCount",
    "likelyJobsCount",
    "unverifiedJobsCount",
    "fallbackJobsCount",
    "officialSourceJobsCount",
    "jobBoardJobsCount",
    "searchResultJobsCount",
    "highMatchVerifiedJobsCount",
    "configuredOfficialCompanies",
    "successfulOfficialCompanies",
    "noMatchingOfficialCompanies",
    "failedOfficialCompanies",
    "officialJobsFound",
    "likelyJobsFound",
    "unverifiedSearchLeads",
    "highMatchJobsCount",
    "genericSearchResultsFiltered",
    "verifiedJobDetailsChecked",
    "verifiedJobsDowngraded",
    "genericHotspotsFiltered",
    "concreteHotspotsKept",
    "jobDetailPagesFailed",
    "jobDetailPagesPassed",
    "failedSources",
    "companyCrawlStatus",
]

GENERIC_HOTSPOT_TITLE_TERMS = [
    "Bing Search",
    "搜索结果",
    "早报合集",
    "多条新闻混合",
    "案例值得加入观察",
    "案例值得加入产品设计观察",
    "热点：产品设计信号",
]

STRONG_DESIGN_JOB_TERMS = [
    "工业设计",
    "产品设计",
    "ID",
    "CMF",
    "硬件产品设计",
    "消费电子",
    "智能硬件",
    "家电",
    "机器人",
    "清洁电器",
    "Industrial Designer",
    "Product Designer",
]


def read_json(path: Path, errors: list[str]) -> Any | None:
    if not path.exists():
        errors.append(f"Missing file: {path.relative_to(ROOT)}")
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON: {path.relative_to(ROOT)} ({exc})")
        return None


def require_keys(name: str, data: dict[str, Any], keys: list[str], errors: list[str]) -> None:
    for key in keys:
        if key not in data:
            errors.append(f"{name} is missing key: {key}")


def validate_report(report: dict[str, Any], report_name: str, errors: list[str]) -> None:
    require_keys(report_name, report, REQUIRED_REPORT_KEYS, errors)
    for key in ["jobOpportunities", "highMatchJobs", "designHotspots", "companyUpdates", "actions"]:
        if key in report and not isinstance(report[key], list):
            errors.append(f"{report_name}.{key} must be a list")

    if "sourceCount" in report and not isinstance(report["sourceCount"], int):
        errors.append(f"{report_name}.sourceCount must be an integer")

    if "totalItems" in report and not isinstance(report["totalItems"], int):
        errors.append(f"{report_name}.totalItems must be an integer")

    if report.get("dataMode") not in {"Real", "Fallback", "Mock"}:
        errors.append(f"{report_name}.dataMode must be Real, Fallback, or Mock")

    if "collectionStatus" in report and report.get("collectionStatus") not in {"success", "partial", "fallback"}:
        errors.append(f"{report_name}.collectionStatus must be success, partial, or fallback")

    if all(key in report for key in ["jobOpportunities", "designHotspots", "companyUpdates", "actions", "totalItems"]):
        expected_total = sum(
            len(report[key])
            for key in ["jobOpportunities", "designHotspots", "companyUpdates", "actions"]
        )
        if report["totalItems"] != expected_total:
            errors.append(
                f"{report_name}.totalItems is {report['totalItems']}, expected {expected_total}"
            )

    quality_report = report.get("qualityReport")
    if not isinstance(quality_report, dict):
        errors.append(f"{report_name}.qualityReport must be an object")
        strict_quality = False
    else:
        require_keys(f"{report_name}.qualityReport", quality_report, REQUIRED_QUALITY_KEYS, errors)
        if not isinstance(quality_report.get("companyCrawlStatus"), list):
            errors.append(f"{report_name}.qualityReport.companyCrawlStatus must be a list")
        if not isinstance(quality_report.get("failedSources"), list):
            errors.append(f"{report_name}.qualityReport.failedSources must be a list")
        strict_quality = quality_report.get("totalCollected", 0) > 0

    for action in report.get("actions", []):
        action_text = f"{action.get('title', '')} {action.get('description', '')} {' '.join(action.get('keywords', []))}"
        if "小红书" in action_text:
            errors.append(f"{report_name}.actions must not contain 小红书 content")

    for key in ["jobOpportunities", "highMatchJobs", "designHotspots", "companyUpdates"]:
        for item_index, item in enumerate(report.get(key, [])):
            item_text = json.dumps(item, ensure_ascii=False)
            if "小红书" in item_text or "社交媒体" in item_text:
                errors.append(f"{report_name}.{key}[{item_index}] contains removed social-media content")

    for item_index, job in enumerate(report.get("jobOpportunities", [])):
        if not isinstance(job, dict):
            continue
        require_keys(f"{report_name}.jobOpportunities[{item_index}]", job, REQUIRED_JOB_KEYS, errors)
        status = job.get("verificationStatus")
        source_type = job.get("sourceType")
        confidence = job.get("confidenceScore", 0)
        match_score = job.get("matchScore", 0)
        if status not in {"verified", "likely", "unverified", "fallback"}:
            errors.append(f"{report_name}.jobOpportunities[{item_index}].verificationStatus is invalid")
        if source_type not in {"official", "job_board", "search_result", "media", "fallback"}:
            errors.append(f"{report_name}.jobOpportunities[{item_index}].sourceType is invalid")
        if status in {"unverified", "fallback"} and match_score >= 90:
            errors.append(f"{report_name}.jobOpportunities[{item_index}] unverified/fallback cannot be 90+")
        if source_type == "search_result" and match_score > 80:
            errors.append(f"{report_name}.jobOpportunities[{item_index}] search_result cannot exceed 80")
        if status == "fallback" and match_score > 65:
            errors.append(f"{report_name}.jobOpportunities[{item_index}] fallback matchScore cannot exceed 65")
        if status == "fallback" and confidence > 50:
            errors.append(f"{report_name}.jobOpportunities[{item_index}] fallback confidence must be <= 50")
        if status == "verified" and confidence < 75:
            errors.append(f"{report_name}.jobOpportunities[{item_index}] verified confidence must be >= 75")
        if status == "likely" and confidence < 75:
            errors.append(f"{report_name}.jobOpportunities[{item_index}] likely confidence must be >= 75")
        if status == "verified":
            detail_text = " ".join(
                [
                    str(job.get("title", "")),
                    str(job.get("responsibilitiesSummary", "")),
                    str(job.get("requirementsSummary", "")),
                    str(job.get("evidenceText", "")),
                ]
            )
            requirements = str(job.get("requirementsSummary", ""))
            has_real_requirements = bool(requirements) and not requirements.startswith(("请打开", "历史日报", "页面未提供"))
            has_role_detail = bool(job.get("responsibilitiesSummary") or has_real_requirements)
            if source_type != "official":
                errors.append(f"{report_name}.jobOpportunities[{item_index}] verified must use official source")
            if not str(job.get("title", "")).strip():
                errors.append(f"{report_name}.jobOpportunities[{item_index}] verified must have a concrete title")
            if not str(job.get("city", "")).strip() or job.get("city") == "全国":
                errors.append(f"{report_name}.jobOpportunities[{item_index}] verified must have a concrete city")
            if not has_role_detail:
                errors.append(f"{report_name}.jobOpportunities[{item_index}] verified must include responsibilities or requirements")
            if not any(term.lower() in detail_text.lower() for term in STRONG_DESIGN_JOB_TERMS):
                errors.append(f"{report_name}.jobOpportunities[{item_index}] verified lacks strong design relevance")

    for item_index, job in enumerate(report.get("highMatchJobs", [])):
        if job.get("matchScore", 0) < 85:
            errors.append(f"{report_name}.highMatchJobs[{item_index}] matchScore must be >= 85")
        if job.get("confidenceScore", 0) < 75:
            errors.append(f"{report_name}.highMatchJobs[{item_index}] confidenceScore must be >= 75")
        if job.get("verificationStatus") not in {"verified", "likely"}:
            errors.append(f"{report_name}.highMatchJobs[{item_index}] must be verified or likely")

    if isinstance(quality_report, dict):
        jobs = [job for job in report.get("jobOpportunities", []) if isinstance(job, dict)]
        high_match_jobs = [job for job in jobs if job.get("matchScore", 0) >= 85 and job.get("confidenceScore", 0) >= 75 and job.get("verificationStatus") in {"verified", "likely"}]
        expected_counts = {
            "verifiedJobsCount": len([job for job in jobs if job.get("verificationStatus") == "verified"]),
            "likelyJobsCount": len([job for job in jobs if job.get("verificationStatus") == "likely"]),
            "unverifiedJobsCount": len([job for job in jobs if job.get("verificationStatus") == "unverified"]),
            "fallbackJobsCount": len([job for job in jobs if job.get("verificationStatus") == "fallback"]),
            "officialSourceJobsCount": len([job for job in jobs if job.get("sourceType") == "official"]),
            "jobBoardJobsCount": len([job for job in jobs if job.get("sourceType") == "job_board"]),
            "searchResultJobsCount": len([job for job in jobs if job.get("sourceType") == "search_result"]),
            "highMatchVerifiedJobsCount": len(high_match_jobs),
            "officialJobsFound": len([job for job in jobs if job.get("verificationStatus") == "verified"]),
            "likelyJobsFound": len([job for job in jobs if job.get("verificationStatus") == "likely"]),
            "unverifiedSearchLeads": len([job for job in jobs if job.get("verificationStatus") == "unverified"]),
            "highMatchJobsCount": len(high_match_jobs),
        }
        for key, expected in expected_counts.items():
            if quality_report.get(key) != expected:
                errors.append(f"{report_name}.qualityReport.{key} is {quality_report.get(key)}, expected {expected}")
        company_status = quality_report.get("companyCrawlStatus", [])
        if isinstance(company_status, list):
            status_counts = {
                "configuredOfficialCompanies": len(company_status),
                "successfulOfficialCompanies": len([item for item in company_status if isinstance(item, dict) and item.get("status") == "success"]),
                "noMatchingOfficialCompanies": len([item for item in company_status if isinstance(item, dict) and item.get("status") == "no_matching_jobs"]),
                "failedOfficialCompanies": len([item for item in company_status if isinstance(item, dict) and item.get("status") == "blocked_or_failed"]),
            }
            for key, expected in status_counts.items():
                if quality_report.get(key) != expected:
                    errors.append(f"{report_name}.qualityReport.{key} is {quality_report.get(key)}, expected {expected}")

    for item_index, hotspot in enumerate(report.get("designHotspots", [])):
        if not isinstance(hotspot, dict):
            continue
        require_keys(f"{report_name}.designHotspots[{item_index}]", hotspot, REQUIRED_HOTSPOT_KEYS, errors)
        if hotspot.get("isGenericSearchResult") is True:
            errors.append(f"{report_name}.designHotspots[{item_index}] must not be a generic search result")
        title = str(hotspot.get("title", ""))
        if any(term.lower() in title.lower() for term in GENERIC_HOTSPOT_TITLE_TERMS):
            errors.append(f"{report_name}.designHotspots[{item_index}] must not use a generic title: {title}")
        if strict_quality and hotspot.get("relevanceScore", 0) < 70 and hotspot.get("source") != "Fallback Rule":
            errors.append(f"{report_name}.designHotspots[{item_index}] relevanceScore must be >= 70")
        if strict_quality and hotspot.get("confidenceScore", 0) < 65 and hotspot.get("source") != "Fallback Rule":
            errors.append(f"{report_name}.designHotspots[{item_index}] confidenceScore must be >= 65")


def validate_data_dir(data_dir: Path, errors: list[str], mirror_label: str = "") -> None:
    latest = read_json(data_dir / "latest.json", errors)
    index = read_json(data_dir / "reportsIndex.json", errors)
    reports_dir = data_dir / "reports"

    if not reports_dir.exists():
        errors.append(f"Missing directory: {reports_dir.relative_to(ROOT)}")

    if isinstance(latest, dict):
        validate_report(latest, f"{mirror_label}latest.json", errors)

    if isinstance(index, list):
        if not index:
            errors.append(f"{mirror_label}reportsIndex.json must not be empty")
        for item_index, item in enumerate(index):
            if not isinstance(item, dict):
                errors.append(f"{mirror_label}reportsIndex[{item_index}] must be an object")
                continue
            require_keys(f"{mirror_label}reportsIndex[{item_index}]", item, REQUIRED_INDEX_KEYS, errors)
    elif index is not None:
        errors.append(f"{mirror_label}reportsIndex.json must be a list")

    if isinstance(latest, dict) and isinstance(index, list) and index:
        newest_date = max(item.get("date", "") for item in index if isinstance(item, dict))
        if latest.get("date") != newest_date:
            errors.append(
                f"{mirror_label}latest.json date {latest.get('date')} does not match newest reportsIndex date {newest_date}"
            )

        for item in index:
            if not isinstance(item, dict) or "date" not in item:
                continue

            report_path = reports_dir / f"{item['date']}.json"
            report = read_json(report_path, errors)
            if not isinstance(report, dict):
                continue

            validate_report(report, f"{mirror_label}reports/{item['date']}.json", errors)
            if report.get("date") != item["date"]:
                errors.append(
                    f"{mirror_label}reports/{item['date']}.json has date {report.get('date')}"
                )
            jobs = report.get("jobOpportunities", report.get("jobs", []))
            hotspots = report.get("designHotspots", report.get("trends", []))
            high_match_jobs = report.get("highMatchJobs") or [job for job in jobs if job.get("matchScore", 0) >= 90]
            if len(hotspots) != item.get("newsCount"):
                errors.append(f"{mirror_label}{item['date']} newsCount does not match designHotspots length")
            if len(jobs) != item.get("jobsCount"):
                errors.append(f"{mirror_label}{item['date']} jobsCount does not match jobOpportunities length")
            if len(hotspots) != item.get("trendsCount"):
                errors.append(f"{mirror_label}{item['date']} trendsCount does not match designHotspots length")
            high_match_count = len(high_match_jobs)
            if high_match_count != item.get("highMatchJobsCount"):
                errors.append(f"{mirror_label}{item['date']} highMatchJobsCount does not match jobs data")


def main() -> int:
    errors: list[str] = []

    if not DATA_DIR.exists():
        errors.append("Missing directory: data")
    else:
        validate_data_dir(DATA_DIR, errors)

    if not PUBLIC_DATA_DIR.exists():
        errors.append("Missing directory: public/data")
    else:
        validate_data_dir(PUBLIC_DATA_DIR, errors, "public/data/")

    if errors:
        print("Data validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Data validation succeeded.")
    print("latest.json, reportsIndex.json, and all report JSON files are consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
