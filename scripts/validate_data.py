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
    "topNews",
    "trends",
    "aiTools",
    "hardwareObservation",
    "jobs",
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
    for key in ["topNews", "trends", "aiTools", "hardwareObservation", "jobs", "actions"]:
        if key in report and not isinstance(report[key], list):
            errors.append(f"{report_name}.{key} must be a list")

    if "sourceCount" in report and not isinstance(report["sourceCount"], int):
        errors.append(f"{report_name}.sourceCount must be an integer")

    if "totalItems" in report and not isinstance(report["totalItems"], int):
        errors.append(f"{report_name}.totalItems must be an integer")

    if all(key in report for key in ["topNews", "trends", "aiTools", "hardwareObservation", "jobs", "actions", "totalItems"]):
        expected_total = sum(
            len(report[key])
            for key in ["topNews", "trends", "aiTools", "hardwareObservation", "jobs", "actions"]
        )
        if report["totalItems"] != expected_total:
            errors.append(
                f"{report_name}.totalItems is {report['totalItems']}, expected {expected_total}"
            )


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
            if len(report.get("topNews", [])) != item.get("newsCount"):
                errors.append(f"{mirror_label}{item['date']} newsCount does not match topNews length")
            if len(report.get("jobs", [])) != item.get("jobsCount"):
                errors.append(f"{mirror_label}{item['date']} jobsCount does not match jobs length")
            if len(report.get("trends", [])) != item.get("trendsCount"):
                errors.append(f"{mirror_label}{item['date']} trendsCount does not match trends length")
            high_match_count = len([job for job in report.get("jobs", []) if job.get("matchScore", 0) >= 90])
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
