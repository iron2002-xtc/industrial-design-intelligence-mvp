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
from summarize_report import build_daily_report

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PUBLIC_DATA_DIR = ROOT / "public" / "data"
REPORT_KEYS = ["topNews", "trends", "aiTools", "hardwareObservation", "jobs", "actions"]


def read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def report_index_item(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "date": report["date"],
        "title": report["title"],
        "summary": report["summary"],
        "newsCount": len(report.get("topNews", [])),
        "jobsCount": len(report.get("jobs", [])),
        "trendsCount": len(report.get("trends", [])),
        "highMatchJobsCount": len([job for job in report.get("jobs", []) if job.get("matchScore", 0) >= 90]),
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


def ensure_report_metadata(report: dict[str, Any]) -> dict[str, Any]:
    report.setdefault("dataMode", "Mock")
    report.setdefault("collectionStatus", "success")
    report.setdefault("statusMessage", "")
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
