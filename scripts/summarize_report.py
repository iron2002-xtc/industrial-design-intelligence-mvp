#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

FIRST_PRIORITY_CITIES = ["深圳", "上海", "杭州", "苏州", "广州", "东莞", "北京", "南京"]
SECOND_PRIORITY_CITIES = [
    "宁波",
    "无锡",
    "常州",
    "佛山",
    "珠海",
    "惠州",
    "中山",
    "厦门",
    "武汉",
    "成都",
    "重庆",
    "西安",
    "青岛",
    "合肥",
    "天津",
    "长沙",
]
THIRD_PRIORITY_CITIES = ["郑州", "济南", "福州", "南昌", "昆明", "沈阳", "大连", "长春", "哈尔滨", "南宁", "贵阳", "太原"]

TARGET_COMPANY_FALLBACKS = [
    ("DJI 大疆", "深圳", "智能硬件", "校招 / 实习 / 社招", "官网招聘", "https://www.dji.com/cn/careers"),
    ("华为", "深圳", "3C", "校招 / 社招", "官网招聘", "https://career.huawei.com/reccampportal/portal5/index.html"),
    ("小米", "北京", "智能硬件", "校招 / 社招", "官网招聘", "https://hr.xiaomi.com/"),
    ("OPPO", "深圳", "CMF", "校招 / 实习 / 社招", "官网招聘", "https://careers.oppo.com/"),
    ("vivo", "东莞", "3C", "校招 / 社招", "官网招聘", "https://hr.vivo.com/"),
    ("荣耀", "深圳", "3C", "校招 / 社招", "官网招聘", "https://career.hihonor.com/"),
    ("Insta360 影石", "深圳", "影像设备", "校招 / 社招", "官网招聘", "https://www.insta360.com/cn/careers"),
    ("云鲸", "深圳", "清洁电器", "校招 / 社招", "官网招聘", "https://www.narwal.com/cn/careers"),
    ("追觅", "苏州", "清洁电器", "校招 / 社招", "官网招聘", "https://www.dreame.tech/cn/careers"),
    ("石头科技", "北京", "机器人", "校招 / 社招", "官网招聘", "https://cn.roborock.com/pages/join-us"),
    ("TCL", "广州", "家电", "校招 / 社招", "官网招聘", "https://campus.tcl.com/"),
    ("美的", "佛山", "家电", "校招 / 社招", "官网招聘", "https://careers.midea.com/"),
    ("海尔", "青岛", "家电", "校招 / 社招", "官网招聘", "https://maker.haier.net/client/join"),
    ("科沃斯", "苏州", "机器人", "校招 / 社招", "官网招聘", "https://www.ecovacs.cn/careers"),
    ("联想", "北京", "3C", "校招 / 社招", "官网招聘", "https://talent.lenovo.com.cn/"),
    ("海信", "青岛", "家电", "校招 / 社招", "官网招聘", "https://hisense.zhiye.com/"),
    ("九号", "北京", "交通工具", "校招 / 社招", "官网招聘", "https://www.ninebot.com/careers"),
    ("安克 Anker", "深圳", "3C", "校招 / 社招", "官网招聘", "https://www.anker.com/careers"),
    ("绿联", "深圳", "3C", "校招 / 社招", "官网招聘", "https://www.ugreen.com/pages/careers"),
    ("倍思 Baseus", "深圳", "3C", "校招 / 社招", "官网招聘", "https://www.baseus.com/pages/careers"),
    ("Apple", "上海", "消费电子", "社招 / 1-3年", "官网招聘", "https://jobs.apple.com/"),
    ("Samsung", "上海", "消费电子", "社招 / 1-3年", "官网招聘", "https://www.samsung.com/global/careers/"),
    ("Dyson", "上海", "家电", "社招 / 1-3年", "官网招聘", "https://careers.dyson.com/"),
    ("Nothing", "深圳", "3C", "社招 / 1-3年", "官网招聘", "https://nothing.tech/pages/careers"),
]

TARGET_COMPANY_NAMES = [company for company, *_ in TARGET_COMPANY_FALLBACKS]
JOB_DIRECTIONS = ["工业设计", "产品设计", "ID设计", "CMF", "设计研究", "3C", "智能硬件", "AI硬件", "家电", "机器人", "清洁电器", "影像设备", "可穿戴设备", "交通工具", "消费电子"]
DESIGN_CATEGORIES = ["工业设计趋势", "3C产品", "智能硬件", "AI硬件", "清洁电器", "机器人", "家电", "影像设备", "可穿戴设备", "交通工具", "消费电子", "CMF", "设计奖项", "优秀产品案例"]
DESIGN_KEYWORDS = ["工业设计", "产品设计", "设计语言", "CMF", "结构创新", "交互体验", "3C", "AI硬件", "智能硬件", "机器人", "家电", "清洁电器", "可穿戴", "影像设备", "消费电子", "发布会", "新品", "设计奖", "红点", "iF", "IDEA", "Good Design"]
DESIGN_MEDIA = {"Dezeen", "Yanko Design", "Core77", "Designboom", "The Verge", "少数派", "爱范儿", "机器之心"}
REALNESS_FACTOR = {
    "verified": 1.0,
    "likely": 0.85,
    "unverified": 0.6,
    "fallback": 0.45,
}
JOB_BOARD_DOMAINS = [
    "zhipin.com",
    "liepin.com",
    "lagou.com",
    "shixiseng.com",
    "nowcoder.com",
    "kanzhun.com",
    "51job.com",
    "zhaopin.com",
    "linkedin.com",
]
OFFICIAL_DOMAIN_HINTS = [
    "dji.com",
    "huawei.com",
    "xiaomi.com",
    "oppo.com",
    "vivo.com",
    "hihonor.com",
    "insta360.com",
    "narwal.com",
    "dreame",
    "roborock.com",
    "tcl.com",
    "midea.com",
    "haier",
    "ecovacs",
    "lenovo.com",
    "hisense",
    "ninebot.com",
    "anker.com",
    "ugreen.com",
    "baseus.com",
]


def clean_text(value: str | None, max_length: int = 220) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()[:max_length]


def has_cjk(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def stable_id(date: str, kind: str, seed: str) -> str:
    digest = hashlib.sha1(f"{date}|{kind}|{seed}".encode("utf-8")).hexdigest()[:10]
    return f"{date}-{kind}-{digest}"


def domain_name(url: str | None) -> str:
    if not url:
        return ""
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except ValueError:
        return ""


def text_blob(item: dict[str, Any]) -> str:
    values = [
        item.get("title", ""),
        item.get("summary", ""),
        item.get("source", ""),
        item.get("category", ""),
        item.get("query", ""),
        item.get("detailTitle", ""),
        item.get("evidenceText", ""),
        " ".join(item.get("keywords", [])),
    ]
    return " ".join(values)


def keyword_score(text: str, keywords: list[str], weight: int = 7) -> int:
    lowered = text.lower()
    return sum(weight for keyword in keywords if keyword.lower() in lowered)


def infer_city(text: str, fallback: str = "全国") -> str:
    for city in [*FIRST_PRIORITY_CITIES, *SECOND_PRIORITY_CITIES, *THIRD_PRIORITY_CITIES]:
        if city in text:
            return city
    return fallback


def city_score(city: str) -> int:
    if city in FIRST_PRIORITY_CITIES:
        return 18
    if city in SECOND_PRIORITY_CITIES:
        return 12
    if city in THIRD_PRIORITY_CITIES:
        return 7
    return 4


def city_tier_label(city: str) -> str:
    if city in FIRST_PRIORITY_CITIES:
        return "一优城市"
    if city in SECOND_PRIORITY_CITIES:
        return "二优城市"
    if city in THIRD_PRIORITY_CITIES:
        return "潜力城市"
    return "全国机会"


def infer_direction(text: str, fallback: str = "工业设计") -> str:
    lowered = text.lower()
    if "cmf" in lowered or "材料" in text or "色彩" in text:
        return "CMF"
    for direction in ["清洁电器", "机器人", "AI硬件", "智能硬件", "影像设备", "可穿戴设备", "交通工具", "消费电子", "家电", "3C", "设计研究", "产品设计", "ID设计"]:
        if direction.lower() in lowered or direction in text:
            return direction
    return fallback


def infer_job_type(text: str, experience: str) -> str:
    combined = f"{text} {experience}"
    if "实习" in combined:
        return "实习"
    if "校招" in combined or "应届" in combined or "硕士" in combined:
        return "校招"
    if "社招" in combined:
        return "社招"
    if "1-3" in combined or "1～3" in combined or "1 至 3" in combined:
        return "1-3年"
    return "可跟进"


def source_quality(item: dict[str, Any], fallback: int = 70) -> int:
    source = item.get("source", "")
    kind = item.get("kind", "")
    if kind == "job_page":
        return 92 if item.get("crawlStatus") == "success" else 62
    if source in DESIGN_MEDIA:
        return 88
    if kind in {"job_search_result", "hotspot_search_result"}:
        if item.get("sourceType") == "official" and item.get("verificationStatus") == "verified":
            return 92
        if item.get("sourceType") == "job_board" and item.get("verificationStatus") == "likely":
            return 84
        return 76 if item.get("detailFetched") else 58
    if source == "Fallback Rule":
        return 50
    return fallback


def source_label(score: int) -> str:
    if score >= 90:
        return "官网来源"
    if score >= 85:
        return "高可信"
    if score >= 70:
        return "可核对来源"
    return "搜索线索"


def detect_source_type(item: dict[str, Any]) -> str:
    if item.get("source") == "Fallback Rule" or item.get("status") == "fallback":
        return "fallback"
    if item.get("kind") == "job_page" or item.get("sourceType") == "official":
        return "official"
    domain = domain_name(item.get("url"))
    if any(hint in domain for hint in OFFICIAL_DOMAIN_HINTS):
        return "official"
    if any(hint in domain for hint in JOB_BOARD_DOMAINS):
        return "job_board"
    if item.get("kind") in {"job_search_result", "hotspot_search_result"}:
        return "search_result"
    if item.get("kind") == "article":
        return "media"
    return "search_result"


def verification_from_evidence(item: dict[str, Any], company: str, city: str, direction: str) -> tuple[str, int]:
    if item.get("verificationStatus") in {"verified", "likely", "unverified", "fallback"} and isinstance(item.get("confidenceScore"), int):
        return item["verificationStatus"], int(item["confidenceScore"])

    source_type = detect_source_type(item)
    if source_type == "fallback":
        return "fallback", 45

    evidence = f"{item.get('title', '')} {item.get('summary', '')} {item.get('evidenceText', '')} {item.get('detailTitle', '')}"
    has_company = company != "公开招聘线索" and (company in evidence or company.split(" ")[0] in evidence)
    has_city = city != "全国" and city in evidence
    has_job_signal = any(keyword in evidence for keyword in ["工业设计", "产品设计", "ID设计", "CMF", "外观设计", "设计师"])

    if source_type == "official" and has_company and has_city and has_job_signal:
        return "verified", 95
    if source_type == "job_board" and item.get("detailFetched") and has_company and has_city and has_job_signal:
        return "likely", 84
    if item.get("detailFetched") and has_job_signal and (has_company or has_city):
        return "likely", 76
    if source_type == "official" and item.get("crawlStatus") == "success" and has_job_signal:
        return "unverified", 68
    if item.get("kind") == "job_search_result":
        return "unverified", 58
    return "unverified", 55


def apply_realness_score(position_score: int, verification_status: str, source_type: str) -> int:
    score = round(position_score * REALNESS_FACTOR.get(verification_status, 0.6))
    if verification_status == "fallback":
        return min(score, 65)
    if verification_status == "unverified":
        return min(score, 80)
    if source_type == "search_result":
        return min(score, 80)
    return min(score, 99)


def canonical_job_title(title: str, direction: str) -> str:
    text = re.sub(r"\s+", "", f"{title}{direction}".lower())
    if "cmf" in text or "色彩" in text or "材料" in text:
        return "cmf"
    if "清洁" in text or "扫地" in text or "洗地" in text:
        return "cleaning-industrial-design"
    if "机器人" in text or "robot" in text:
        return "robot-industrial-design"
    if "家电" in text or "电器" in text:
        return "appliance-industrial-design"
    if "影像" in text or "相机" in text or "camera" in text:
        return "camera-industrial-design"
    if "3c" in text or "手机" in text or "消费电子" in text:
        return "3c-industrial-design"
    if "产品设计" in text:
        return "product-design"
    if "工业设计" in text or "id设计" in text or "外观设计" in text:
        return "industrial-design"
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", text)[:24] or "industrial-design"


def dedupe_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for job in jobs:
        key = f"{job.get('company')}|{job.get('city')}|{canonical_job_title(job.get('title', ''), job.get('direction', ''))}"
        current = unique.get(key)
        if current is None:
            unique[key] = job
            continue
        current_rank = (current.get("confidenceScore", 0), current.get("matchScore", 0), current.get("sourceQualityScore", 0))
        next_rank = (job.get("confidenceScore", 0), job.get("matchScore", 0), job.get("sourceQualityScore", 0))
        if next_rank > current_rank:
            unique[key] = job
    return list(unique.values())


def infer_company(text: str, fallback: str = "公开招聘线索") -> str:
    for company in TARGET_COMPANY_NAMES:
        aliases = [company, company.split(" ")[0]]
        if "DJI" in company:
            aliases.append("大疆")
        if "Insta360" in company:
            aliases.append("影石")
        if "Baseus" in company:
            aliases.append("倍思")
        if "Anker" in company:
            aliases.append("安克")
        if any(alias and alias in text for alias in aliases):
            return company
    return fallback


def job_match_score(company: str, city: str, direction: str, job_type: str, source_score: int, text: str) -> tuple[int, int]:
    target_score = 25 if company in TARGET_COMPANY_NAMES else 10
    direction_score = 22 if any(keyword in direction for keyword in ["工业设计", "产品设计", "ID", "CMF"]) else 16
    if direction in ["3C", "智能硬件", "AI硬件", "家电", "机器人", "清洁电器", "影像设备", "可穿戴设备", "消费电子"]:
        direction_score += 6
    experience_score = 12 if job_type in ["校招", "实习", "1-3年"] else 7
    relevance_score = min(100, 45 + keyword_score(text, ["工业设计师", "工业设计", "产品设计师", "ID设计师", "CMF设计师", "硬件产品设计师", "设计研究"], 8))
    final_score = min(99, target_score + city_score(city) + direction_score + experience_score + round(source_score * 0.16) + 10)
    return final_score, relevance_score


def build_job_reason(job: dict[str, Any], source_text: str) -> str:
    city_label = city_tier_label(job["city"])
    source_part = {
        "verified": "官网可验证，页面能看到岗位/公司/城市证据",
        "likely": "来源较可信，已打开详情页提取到岗位线索",
        "unverified": "搜索或官网入口待核实，尚未验证完整岗位详情",
        "fallback": "备用数据，不作为优先投递依据",
    }.get(job.get("verificationStatus", "unverified"), "来源待核实")
    exp_part = "偏应届/初级经验" if job["jobType"] in ["校招", "实习", "1-3年"] else "需要进一步核对经验要求"
    return (
        f"该岗位位于{job['city']}，属于{job['direction']}方向，{city_label}和方向匹配；"
        f"岗位类型为{job['jobType']}，{exp_part}；{source_part}。"
        f"匹配分已按真实性系数折算，建议先打开原始链接核对是否可投。"
    )


def build_job_from_company_page(item: dict[str, Any], date: str) -> dict[str, Any]:
    company = item.get("company") or infer_company(text_blob(item))
    city = item.get("city") or infer_city(text_blob(item))
    direction = item.get("direction") or infer_direction(text_blob(item))
    experience = item.get("experience") or "校招 / 社招 / 实习"
    job_type = infer_job_type(text_blob(item), experience)
    source_score = source_quality(item)
    position_score, relevance_score = job_match_score(company, city, direction, job_type, source_score, text_blob(item))
    verification_status, confidence_score = verification_from_evidence(item, company, city, direction)
    source_type = detect_source_type(item)
    match_score = apply_realness_score(position_score, verification_status, source_type)
    title_map = {
        "CMF": "CMF / 工业设计机会跟踪",
        "清洁电器": "清洁电器工业设计机会跟踪",
        "机器人": "机器人产品设计机会跟踪",
        "家电": "家电产品设计机会跟踪",
        "影像设备": "影像设备产品设计机会跟踪",
        "交通工具": "出行产品工业设计机会跟踪",
    }
    job = {
        "id": stable_id(date, "job", company),
        "company": company,
        "title": title_map.get(direction, "工业设计 / 产品设计机会跟踪"),
        "city": city,
        "direction": direction,
        "experience": experience,
        "jobType": job_type,
        "matchScore": match_score,
        "sourceQualityScore": source_score,
        "relevanceScore": relevance_score,
        "reason": "",
        "requirementsSummary": f"重点核对岗位是否要求工业设计、产品设计、CMF、结构理解、渲染表达和作品集完整项目叙事。",
        "url": item.get("url"),
        "verificationStatus": verification_status,
        "sourceType": source_type,
        "applyUrl": item.get("url"),
        "originalUrl": item.get("url"),
        "evidenceText": clean_text(item.get("evidenceText") or item.get("summary"), 220),
        "lastCheckedAt": item.get("lastCheckedAt"),
        "confidenceScore": confidence_score,
        "date": date,
        "tags": [source_label(source_score), verification_status, source_type, job_type, direction, city_tier_label(city)],
        "keywords": [company, city, direction, job_type, "工业设计", "招聘"],
    }
    job["reason"] = build_job_reason(job, text_blob(item))
    return job


def build_job_from_search(item: dict[str, Any], date: str) -> dict[str, Any]:
    blob = text_blob(item)
    company = item.get("company") or infer_company(blob)
    city = item.get("city") or infer_city(blob, "全国")
    direction = infer_direction(blob)
    experience = "应届 / 实习 / 1-3年可核对"
    job_type = infer_job_type(blob, experience)
    source_score = source_quality(item)
    position_score, relevance_score = job_match_score(company, city, direction, job_type, source_score, blob)
    verification_status, confidence_score = verification_from_evidence(item, company, city, direction)
    source_type = detect_source_type(item)
    match_score = apply_realness_score(position_score, verification_status, source_type)
    title = clean_text(item.get("title"), 80) or f"{direction}招聘线索"
    job = {
        "id": stable_id(date, "job-search", item.get("id") or title),
        "company": company,
        "title": title,
        "city": city,
        "direction": direction,
        "experience": experience,
        "jobType": job_type,
        "matchScore": max(40, match_score - (8 if source_type == "search_result" else 0)),
        "sourceQualityScore": source_score,
        "relevanceScore": relevance_score,
        "reason": "",
        "requirementsSummary": clean_text(item.get("summary"), 120) or "来自公开搜索结果，需点开原始链接核对岗位职责和经验要求。",
        "url": item.get("url"),
        "verificationStatus": verification_status,
        "sourceType": source_type,
        "applyUrl": item.get("url") if verification_status in {"verified", "likely"} else "",
        "originalUrl": item.get("url"),
        "evidenceText": clean_text(item.get("evidenceText") or item.get("summary"), 220),
        "lastCheckedAt": item.get("lastCheckedAt") or item.get("publishedDate"),
        "confidenceScore": confidence_score,
        "date": date,
        "tags": [source_label(source_score), verification_status, source_type, job_type, direction, city_tier_label(city)],
        "keywords": [company, city, direction, job_type, "招聘"],
    }
    job["reason"] = build_job_reason(job, blob)
    return job


def has_real_job_signal(item: dict[str, Any]) -> bool:
    evidence = " ".join(
        [
            item.get("title", ""),
            item.get("summary", ""),
            item.get("detailTitle", ""),
            item.get("evidenceText", ""),
        ]
    )
    return item.get("detailFetched") and any(
        keyword in evidence
        for keyword in ["工业设计", "产品设计", "ID设计", "CMF", "外观设计", "设计师", "Industrial Designer", "Product Designer"]
    )


def build_job_opportunities(items: list[dict[str, Any]], date: str) -> list[dict[str, Any]]:
    company_pages = [item for item in items if item.get("kind") == "job_page" and item.get("crawlStatus") == "success"]
    search_results = [item for item in items if item.get("kind") == "job_search_result" and has_real_job_signal(item)]
    jobs = [build_job_from_company_page(item, date) for item in company_pages]
    jobs.extend(build_job_from_search(item, date) for item in search_results[:8])
    if not jobs:
        jobs = [
            build_job_from_company_page(
                {
                    "kind": "job_page",
                    "company": company,
                    "city": city,
                    "direction": direction,
                    "experience": experience,
                    "url": url,
                    "source": "Fallback Rule",
                    "status": "fallback",
                    "keywords": [company, city, direction],
                },
                date,
            )
            for company, city, direction, experience, _, url in TARGET_COMPANY_FALLBACKS
        ]
    return sorted(dedupe_jobs(jobs), key=lambda item: item["matchScore"], reverse=True)[:28]


def infer_hotspot_category(text: str, fallback: str = "工业设计趋势") -> str:
    lowered = text.lower()
    checks = [
        ("CMF", ["cmf", "材质", "材料", "色彩", "工艺"]),
        ("设计奖项", ["红点", "reddot", "if设计", "idea", "good design", "设计奖"]),
        ("AI硬件", ["ai硬件", "ai hardware", "端侧ai"]),
        ("3C产品", ["3c", "手机", "phone", "电脑", "camera", "耳机"]),
        ("智能硬件", ["智能硬件", "smart hardware", "iot"]),
        ("清洁电器", ["清洁", "扫地", "洗地", "vacuum"]),
        ("机器人", ["机器人", "robot", "robotics"]),
        ("家电", ["家电", "appliance", "home appliance"]),
        ("影像设备", ["影像", "相机", "camera", "action cam"]),
        ("可穿戴设备", ["可穿戴", "wearable", "watch", "眼镜"]),
        ("交通工具", ["出行", "vehicle", "scooter", "交通工具"]),
        ("消费电子", ["consumer electronics", "消费电子"]),
    ]
    for category, keywords in checks:
        if any(keyword in lowered or keyword in text for keyword in keywords):
            return category
    return fallback


def related_companies(text: str) -> list[str]:
    result = []
    for company in TARGET_COMPANY_NAMES:
        if company in text or company.split(" ")[0] in text:
            result.append(company)
    return result[:4]


def hotspot_relevance(item: dict[str, Any], category: str) -> tuple[int, int]:
    blob = text_blob(item)
    source_score = source_quality(item, 72)
    relevance = 45 + keyword_score(blob, DESIGN_KEYWORDS, 7)
    if category in DESIGN_CATEGORIES:
        relevance += 12
    if related_companies(blob):
        relevance += 10
    if item.get("kind") == "hotspot_search_result":
        relevance += 5 if item.get("detailFetched") else -25
    return min(98, relevance), source_score


def has_real_hotspot_signal(item: dict[str, Any]) -> bool:
    evidence = " ".join(
        [
            item.get("title", ""),
            item.get("summary", ""),
            item.get("detailTitle", ""),
            item.get("evidenceText", ""),
            item.get("source", ""),
        ]
    )
    return any(keyword.lower() in evidence.lower() or keyword in evidence for keyword in DESIGN_KEYWORDS)


def chinese_title(source: str, category: str, raw_title: str) -> str:
    if raw_title and has_cjk(raw_title):
        return raw_title
    if raw_title:
        return f"{source}：{category}案例值得加入产品设计观察"
    return f"{category}热点：产品设计信号值得跟进"


def chinese_summary(category: str, raw_title: str, raw_summary: str) -> str:
    if raw_summary and has_cjk(raw_summary):
        return raw_summary
    if raw_summary:
        return f"公开来源提到“{raw_title}”。这条信息与{category}相关，可作为产品设计趋势、竞品语言或作品集调研线索。"
    return f"今日出现与{category}相关的公开产品设计信号，适合继续核对原文和产品图。"


def build_design_hotspots(items: list[dict[str, Any]], date: str) -> list[dict[str, Any]]:
    candidates = [item for item in items if item.get("kind") in {"article", "hotspot_search_result"}]
    hotspots: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in candidates:
        is_search = item.get("kind") == "hotspot_search_result"
        if is_search and not item.get("detailFetched"):
            continue
        if is_search and not has_real_hotspot_signal(item):
            continue
        raw_title = clean_text(item.get("title"), 90)
        blob = text_blob(item)
        category = infer_hotspot_category(blob, item.get("category") or "工业设计趋势")
        relevance, source_score = hotspot_relevance(item, category)
        confidence_score = source_score
        if relevance < 70 or confidence_score < 65:
            continue
        key = item.get("url") or raw_title
        if key in seen:
            continue
        seen.add(key)
        source = item.get("source") or "Public Source"
        companies = related_companies(blob)
        hotspots.append(
            {
                "id": stable_id(date, "hotspot", item.get("id") or raw_title),
                "title": chinese_title(source, category, raw_title),
                "summary": chinese_summary(category, raw_title, clean_text(item.get("summary"), 170)),
                "source": source,
                "category": category,
                "url": item.get("url") or "https://github.com/iron2002-xtc/industrial-design-intelligence-mvp",
                "date": date,
                "importanceScore": min(98, relevance + 3),
                "sourceQualityScore": source_score,
                "relevanceScore": relevance,
                "confidenceScore": confidence_score,
                "designInsight": f"建议把它拆成“场景需求、形态/结构约束、CMF与交互细节、对作品集的启发”四个点记录。",
                "designRelevanceReason": f"来源内容命中{category}与产品设计关键词，具备可追溯原始链接。",
                "productCategory": category,
                "relatedBrand": "、".join(companies) if companies else source,
                "isGenericSearchResult": False,
                "evidenceText": clean_text(item.get("evidenceText") or item.get("summary"), 220),
                "relatedCompanies": companies,
                "tags": [category, source_label(source_score), "设计热点", *companies[:2]],
            }
        )
    if not hotspots:
        hotspots.extend(fallback_hotspots(date, 3))
    return sorted(hotspots, key=lambda item: (item["relevanceScore"], item["sourceQualityScore"]), reverse=True)[:12]


def fallback_hotspots(date: str, count: int) -> list[dict[str, Any]]:
    seeds = [
        ("CMF", "CMF 趋势继续强调低饱和色、微纹理和耐用触感", ["Apple", "Samsung"]),
        ("3C产品", "3C产品设计回到轻薄比例、握持细节和镜头模组秩序", ["小米", "OPPO"]),
        ("AI硬件", "AI硬件从概念演示转向随身场景和可靠交互入口", ["华为", "Nothing"]),
        ("清洁电器", "清洁电器设计重点转向基站尺度、维护路径和家居融合", ["追觅", "云鲸"]),
        ("机器人", "家庭机器人需要更清晰的灯语、姿态和安全感表达", ["科沃斯", "石头科技"]),
        ("设计奖项", "设计奖项案例适合补充产品细节、结构创新和可持续材料观察", ["Dyson", "Apple"]),
    ]
    result = []
    for index, (category, title, companies) in enumerate(seeds[:count]):
        result.append(
            {
                "id": stable_id(date, "fallback-hotspot", category),
                "title": title,
                "summary": "真实来源不足时保留的高相关设计观察框架，后续会被公开来源自动替换。",
                "source": "Fallback Rule",
                "category": category,
                "url": "https://github.com/iron2002-xtc/industrial-design-intelligence-mvp",
                "date": date,
                "importanceScore": 78 - index,
                "sourceQualityScore": 50,
                "relevanceScore": 76 - index,
                "confidenceScore": 50,
                "designInsight": "可作为作品集调研页的备用主题，重点补图、补竞品、补设计判断。",
                "designRelevanceReason": "备用趋势框架，不代表今日真实来源。",
                "productCategory": category,
                "relatedBrand": "、".join(companies),
                "isGenericSearchResult": False,
                "evidenceText": "真实来源不足时使用的备用趋势框架。",
                "relatedCompanies": companies,
                "tags": [category, "作品集参考", "备用数据"],
            }
        )
    return result


def build_company_updates(jobs: list[dict[str, Any]], hotspots: list[dict[str, Any]], date: str) -> list[dict[str, Any]]:
    updates: dict[str, dict[str, Any]] = {}
    for job in jobs:
        if job["company"] not in TARGET_COMPANY_NAMES:
            continue
        updates[job["company"]] = {
            "id": stable_id(date, "company", job["company"]),
            "company": job["company"],
            "title": f"{job['company']}：{job['direction']}岗位入口值得核对",
            "summary": f"{job['city']} / {job['jobType']} / 匹配度 {job['matchScore']}，建议查看原始招聘链接确认岗位是否开放。",
            "category": "招聘",
            "url": job["url"],
            "date": date,
            "relevanceScore": job["matchScore"],
            "designRelation": f"与{job['direction']}、作品集项目选择和求职投递优先级直接相关。",
            "tags": [job["direction"], job["jobType"], source_label(job["sourceQualityScore"])],
        }
    for hotspot in hotspots:
        for company in hotspot.get("relatedCompanies", []):
            if company in updates:
                continue
            updates[company] = {
                "id": stable_id(date, "company-hotspot", company),
                "company": company,
                "title": f"{company}：产品设计动态值得跟进",
                "summary": hotspot["summary"],
                "category": "产品设计动态",
                "url": hotspot["url"],
                "date": date,
                "relevanceScore": hotspot["relevanceScore"],
                "designRelation": hotspot["designInsight"],
                "tags": [hotspot["category"], "设计热点", source_label(hotspot["sourceQualityScore"])],
            }
    return sorted(updates.values(), key=lambda item: item["relevanceScore"], reverse=True)[:8]


def build_actions(report: dict[str, Any]) -> list[dict[str, Any]]:
    top_job = report["highMatchJobs"][0] if report["highMatchJobs"] else report["jobOpportunities"][0]
    top_hotspot = report["designHotspots"][0]
    top_company = report["companyUpdates"][0] if report["companyUpdates"] else None
    actions = [
        {
            "id": stable_id(report["date"], "action", "job"),
            "title": "今日建议重点关注的岗位",
            "description": f"优先打开 {top_job['company']} 的原始链接，核对{top_job['city']} / {top_job['direction']} / {top_job['jobType']}是否可投。",
            "priority": "high",
            "keywords": ["求职", top_job["company"], top_job["city"], top_job["direction"]],
        },
        {
            "id": stable_id(report["date"], "action", "hotspot"),
            "title": "今日建议收藏的设计热点",
            "description": f"收藏“{top_hotspot['title']}”，把它拆成场景、形态、CMF、交互四个观察点。",
            "priority": "medium",
            "keywords": ["设计热点", top_hotspot["category"], "作品集参考"],
        },
        {
            "id": stable_id(report["date"], "action", "portfolio"),
            "title": "今日适合补充到作品集调研的案例",
            "description": f"围绕{top_hotspot['category']}补一页竞品矩阵，重点写清楚设计语言变化和你自己的判断。",
            "priority": "medium",
            "keywords": ["作品集", "设计研究", top_hotspot["category"]],
        },
    ]
    if top_company:
        actions.append(
            {
                "id": stable_id(report["date"], "action", "company"),
                "title": "今日建议跟进的公司动态",
                "description": f"跟进 {top_company['company']}：{top_company['designRelation']}",
                "priority": "low",
                "keywords": ["公司动态", top_company["company"], top_company["category"]],
            }
        )
    return actions


def to_legacy_news(hotspot: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": hotspot["id"],
        "title": hotspot["title"],
        "summary": hotspot["summary"],
        "source": hotspot["source"],
        "category": hotspot["category"],
        "url": hotspot["url"],
        "date": hotspot["date"],
        "importanceScore": hotspot["importanceScore"],
        "designInsight": hotspot["designInsight"],
        "keywords": hotspot["tags"],
    }


def to_legacy_trend(hotspot: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"{hotspot['id']}-trend",
        "title": hotspot["title"],
        "trendSummary": hotspot["summary"],
        "relatedCases": hotspot.get("relatedCompanies") or [hotspot["source"]],
        "designInspiration": hotspot["designInsight"],
        "category": hotspot["category"],
        "url": hotspot["url"],
        "date": hotspot["date"],
        "keywords": hotspot["tags"],
    }


def total_items(report: dict[str, Any]) -> int:
    return sum(len(report.get(key, [])) for key in ["jobOpportunities", "designHotspots", "companyUpdates", "actions"])


def clone_previous_as_fallback(previous_report: dict[str, Any], date: str, generated_at: str, message: str) -> dict[str, Any]:
    report = copy.deepcopy(previous_report)
    report["date"] = date
    report["title"] = f"{date} 工业设计求职与设计热点日报"
    report["summary"] = "今日部分数据抓取失败，已使用上一期求职与设计热点备用数据。"
    report["generatedAt"] = generated_at
    report["dataMode"] = "Fallback"
    report["collectionStatus"] = "fallback"
    report["statusMessage"] = message
    report.setdefault("jobOpportunities", report.get("jobs", []))
    report.setdefault("highMatchJobs", [job for job in report["jobOpportunities"] if is_high_match_job(job)])
    report.setdefault("designHotspots", [to_hotspot_from_legacy_news(item) for item in report.get("topNews", [])])
    report.setdefault("companyUpdates", build_company_updates(report["jobOpportunities"], report["designHotspots"], date))
    report.setdefault(
        "qualityReport",
        {
            "totalCollected": 0,
            "afterDedup": 0,
            "afterQualityFilter": len(report.get("jobOpportunities", [])) + len(report.get("designHotspots", [])),
            "verifiedJobsCount": len([job for job in report.get("jobOpportunities", []) if job.get("verificationStatus") == "verified"]),
            "likelyJobsCount": len([job for job in report.get("jobOpportunities", []) if job.get("verificationStatus") == "likely"]),
            "unverifiedJobsCount": len([job for job in report.get("jobOpportunities", []) if job.get("verificationStatus", "unverified") == "unverified"]),
            "fallbackJobsCount": len([job for job in report.get("jobOpportunities", []) if job.get("verificationStatus") == "fallback"]),
            "officialSourceJobsCount": len([job for job in report.get("jobOpportunities", []) if job.get("sourceType") == "official"]),
            "jobBoardJobsCount": len([job for job in report.get("jobOpportunities", []) if job.get("sourceType") == "job_board"]),
            "searchResultJobsCount": len([job for job in report.get("jobOpportunities", []) if job.get("sourceType") == "search_result"]),
            "highMatchVerifiedJobsCount": len([job for job in report.get("jobOpportunities", []) if is_high_match_job(job)]),
            "configuredOfficialCompanies": len(report.get("qualityReport", {}).get("companyCrawlStatus", [])),
            "successfulOfficialCompanies": len([item for item in report.get("qualityReport", {}).get("companyCrawlStatus", []) if item.get("status") == "success"]),
            "noMatchingOfficialCompanies": len([item for item in report.get("qualityReport", {}).get("companyCrawlStatus", []) if item.get("status") == "no_matching_jobs"]),
            "failedOfficialCompanies": len([item for item in report.get("qualityReport", {}).get("companyCrawlStatus", []) if item.get("status") == "blocked_or_failed"]),
            "officialJobsFound": len([job for job in report.get("jobOpportunities", []) if job.get("verificationStatus") == "verified"]),
            "likelyJobsFound": len([job for job in report.get("jobOpportunities", []) if job.get("verificationStatus") == "likely"]),
            "unverifiedSearchLeads": len([job for job in report.get("jobOpportunities", []) if job.get("verificationStatus") == "unverified"]),
            "highMatchJobsCount": len([job for job in report.get("jobOpportunities", []) if is_high_match_job(job)]),
            "genericSearchResultsFiltered": 0,
            "failedSources": [message],
            "companyCrawlStatus": [],
        },
    )
    for key in ["jobOpportunities", "highMatchJobs", "designHotspots", "companyUpdates"]:
        for item in report.get(key, []):
            item["date"] = date
    report["actions"] = build_actions(report)
    report["totalItems"] = total_items(report)
    return report


def to_hotspot_from_legacy_news(item: dict[str, Any]) -> dict[str, Any]:
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


def try_openai_refine(report: dict[str, Any], collected_items: list[dict[str, Any]]) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return report
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        prompt = {
            "task": "请基于求职岗位和设计热点，为工业设计求职者生成一句中文 qualitySummary。不要出现小红书、社媒运营或泛泛商业新闻。",
            "jobs": report["jobOpportunities"][:8],
            "hotspots": report["designHotspots"][:8],
            "sources": collected_items[:12],
        }
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            input=json.dumps(prompt, ensure_ascii=False),
        )
        text = clean_text(getattr(response, "output_text", ""), 180)
        if text:
            report["qualitySummary"] = text
        return report
    except Exception:  # noqa: BLE001 - optional refinement must never break the update.
        report["statusMessage"] = f"{report.get('statusMessage', '')} OpenAI 摘要失败，已使用规则摘要。".strip()
        return report


def is_high_match_job(job: dict[str, Any]) -> bool:
    return (
        job.get("matchScore", 0) >= 85
        and job.get("confidenceScore", 0) >= 75
        and job.get("verificationStatus") in {"verified", "likely"}
    )


def build_quality_report(
    collected: dict[str, Any],
    job_opportunities: list[dict[str, Any]],
    design_hotspots: list[dict[str, Any]],
) -> dict[str, Any]:
    items = collected.get("items", [])
    unique_urls = {item.get("url") or item.get("id") for item in items}
    included_hotspot_urls = {item.get("url") for item in design_hotspots}
    included_job_urls = {item.get("originalUrl") or item.get("url") for item in job_opportunities}
    hotspot_search_results = [item for item in items if item.get("kind") == "hotspot_search_result"]
    job_search_results = [item for item in items if item.get("kind") == "job_search_result"]
    generic_search_filtered = len(
        [
            item
            for item in hotspot_search_results
            if not item.get("detailFetched") or item.get("url") not in included_hotspot_urls
        ]
    ) + len(
        [
            item
            for item in job_search_results
            if not item.get("detailFetched") or item.get("url") not in included_job_urls
        ]
    )
    failed_sources = [
        log
        for log in collected.get("logs", [])
        if log.startswith("SKIP") or log.startswith("WARN")
    ]
    company_status = collected.get("companyCrawlStatus", [])
    high_match_count = len([job for job in job_opportunities if is_high_match_job(job)])
    return {
        "totalCollected": len(items),
        "afterDedup": len(unique_urls),
        "afterQualityFilter": len(job_opportunities) + len(design_hotspots),
        "verifiedJobsCount": len([job for job in job_opportunities if job.get("verificationStatus") == "verified"]),
        "likelyJobsCount": len([job for job in job_opportunities if job.get("verificationStatus") == "likely"]),
        "unverifiedJobsCount": len([job for job in job_opportunities if job.get("verificationStatus") == "unverified"]),
        "fallbackJobsCount": len([job for job in job_opportunities if job.get("verificationStatus") == "fallback"]),
        "officialSourceJobsCount": len([job for job in job_opportunities if job.get("sourceType") == "official"]),
        "jobBoardJobsCount": len([job for job in job_opportunities if job.get("sourceType") == "job_board"]),
        "searchResultJobsCount": len([job for job in job_opportunities if job.get("sourceType") == "search_result"]),
        "highMatchVerifiedJobsCount": high_match_count,
        "genericSearchResultsFiltered": generic_search_filtered,
        "configuredOfficialCompanies": len(company_status),
        "successfulOfficialCompanies": len([item for item in company_status if item.get("status") == "success"]),
        "noMatchingOfficialCompanies": len([item for item in company_status if item.get("status") == "no_matching_jobs"]),
        "failedOfficialCompanies": len([item for item in company_status if item.get("status") == "blocked_or_failed"]),
        "officialJobsFound": len([job for job in job_opportunities if job.get("verificationStatus") == "verified"]),
        "likelyJobsFound": len([job for job in job_opportunities if job.get("verificationStatus") == "likely"]),
        "unverifiedSearchLeads": len([job for job in job_opportunities if job.get("verificationStatus") == "unverified"]),
        "highMatchJobsCount": high_match_count,
        "failedSources": failed_sources,
        "companyCrawlStatus": company_status,
    }


def build_daily_report(
    collected: dict[str, Any],
    date: str,
    generated_at: str,
    previous_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    items = collected.get("items", [])
    status = collected.get("status", "fallback")
    job_signal_count = len([item for item in items if item.get("kind") in {"job_page", "job_search_result"}])
    hotspot_signal_count = len([item for item in items if item.get("kind") in {"article", "hotspot_search_result"}])

    if not items and previous_report:
        return clone_previous_as_fallback(previous_report, date, generated_at, "今日部分数据抓取失败，已使用备用数据。")

    job_opportunities = build_job_opportunities(items, date)
    high_match_jobs = [job for job in job_opportunities if is_high_match_job(job)]
    design_hotspots = build_design_hotspots(items, date)
    company_updates = build_company_updates(job_opportunities, design_hotspots, date)
    quality_report = build_quality_report(collected, job_opportunities, design_hotspots)
    data_mode = "Real" if job_signal_count >= 4 and hotspot_signal_count >= 3 else "Fallback"
    collection_status = status if data_mode == "Real" and status in {"success", "partial"} else "fallback"
    if collection_status == "success":
        status_message = ""
    elif data_mode == "Fallback":
        status_message = "今日关键源抓取不足，已使用备用数据。"
    else:
        status_message = "今日部分源抓取失败，已保留可验证岗位与设计热点；未通过详情验证的搜索结果已过滤。"

    report = {
        "date": date,
        "title": f"{date} 工业设计求职与设计热点日报",
        "summary": f"今日优先看 {high_match_jobs[0]['company'] if high_match_jobs else job_opportunities[0]['company']} 岗位与 {design_hotspots[0]['category']} 设计热点。",
        "generatedAt": generated_at,
        "dataMode": data_mode,
        "collectionStatus": collection_status,
        "statusMessage": status_message,
        "sourceCount": int(collected.get("sourceCount", 0)),
        "totalItems": 0,
        "qualitySummary": (
            f"今日收集 {quality_report['totalCollected']} 条，过滤 {quality_report['totalCollected'] - quality_report['afterQualityFilter']} 条，"
            f"官网/高可信岗位 {quality_report['verifiedJobsCount'] + quality_report['likelyJobsCount']} 个，"
            f"待核实岗位 {quality_report['unverifiedJobsCount']} 个。"
        ),
        "qualityReport": quality_report,
        "jobOpportunities": job_opportunities,
        "highMatchJobs": high_match_jobs,
        "designHotspots": design_hotspots,
        "companyUpdates": company_updates,
        "actions": [],
    }
    report["actions"] = build_actions(report)
    report["totalItems"] = total_items(report)

    # Legacy mirrors keep older frontend/search/history code resilient.
    report["jobs"] = job_opportunities
    report["topNews"] = [to_legacy_news(item) for item in design_hotspots[:5]]
    report["trends"] = [to_legacy_trend(item) for item in design_hotspots]
    report["aiTools"] = []
    report["hardwareObservation"] = [to_legacy_news(item) for item in design_hotspots if item["category"] in {"智能硬件", "AI硬件", "机器人", "清洁电器"}][:3]
    return try_openai_refine(report, items)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize collected sources into DailyReport JSON.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--date", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--previous", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    collected = json.loads(args.input.read_text(encoding="utf-8"))
    previous = None
    if args.previous and args.previous.exists():
        previous = json.loads(args.previous.read_text(encoding="utf-8"))

    report = build_daily_report(collected, args.date, args.generated_at, previous)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {args.output.relative_to(ROOT)}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
