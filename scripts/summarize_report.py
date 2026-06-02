#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TREND_CATEGORIES = [
    "AI硬件",
    "3C产品",
    "清洁电器",
    "机器人",
    "家电",
    "CMF",
    "AI辅助设计工具",
    "工业设计作品集案例",
]

TARGET_COMPANY_FALLBACKS = [
    ("DJI 大疆", "深圳", "智能硬件", "校招 / 实习 / 社招", "https://www.dji.com/cn/careers"),
    ("华为", "深圳", "3C", "校招 / 社招", "https://career.huawei.com/reccampportal/portal5/index.html"),
    ("小米", "上海", "智能硬件", "校招 / 社招", "https://hr.xiaomi.com/"),
    ("OPPO", "深圳", "CMF", "校招 / 实习 / 社招", "https://careers.oppo.com/"),
    ("vivo", "深圳", "3C", "校招 / 社招", "https://hr.vivo.com/"),
    ("Insta360 影石", "深圳", "3C", "校招 / 社招", "https://www.insta360.com/cn/careers"),
    ("云鲸", "深圳", "清洁电器", "校招 / 社招", "https://www.narwal.com/cn/careers"),
    ("追觅", "苏州", "清洁电器", "校招 / 社招", "https://www.dreame.tech/cn/careers"),
    ("石头科技", "上海", "机器人", "校招 / 社招", "https://cn.roborock.com/pages/join-us"),
    ("TCL", "广州", "家电", "校招 / 社招", "https://campus.tcl.com/"),
    ("美的", "广州", "家电", "校招 / 社招", "https://careers.midea.com/"),
    ("海尔", "南京", "CMF", "校招 / 社招", "https://maker.haier.net/client/join"),
    ("科沃斯", "苏州", "机器人", "校招 / 社招", "https://www.ecovacs.cn/careers"),
]

CATEGORY_KEYWORDS = {
    "AI硬件": ["ai hardware", "ai硬件", "wearable", "智能眼镜", "端侧ai", "机器人"],
    "3C产品": ["3c", "phone", "手机", "laptop", "camera", "consumer electronics", "耳机", "影像"],
    "清洁电器": ["清洁", "扫地", "洗地", "vacuum", "基站", "mop"],
    "机器人": ["robot", "机器人", "robotics", "具身智能"],
    "家电": ["家电", "appliance", "home", "smart home", "智慧家庭"],
    "CMF": ["cmf", "material", "color", "finish", "材质", "工艺", "色彩"],
    "AI辅助设计工具": ["ai design", "design tool", "生成式", "workflow", "工具"],
    "工业设计作品集案例": ["industrial design", "product design", "portfolio", "dezeen", "core77", "designboom", "yanko"],
}


def clean_text(value: str | None, max_length: int = 220) -> str:
    if not value:
        return ""
    text = re.sub(r"\s+", " ", value).strip()
    return text[:max_length]


def has_cjk(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def stable_id(date: str, kind: str, seed: str) -> str:
    digest = hashlib.sha1(f"{date}|{kind}|{seed}".encode("utf-8")).hexdigest()[:10]
    return f"{date}-{kind}-{digest}"


def text_blob(item: dict[str, Any]) -> str:
    values = [
        item.get("title", ""),
        item.get("summary", ""),
        item.get("source", ""),
        item.get("category", ""),
        " ".join(item.get("keywords", [])),
    ]
    return " ".join(values).lower()


def choose_category(item: dict[str, Any]) -> str:
    blob = text_blob(item)
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword.lower() in blob for keyword in keywords):
            return category
    return str(item.get("category") or "工业设计作品集案例")


def sort_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def score(item: dict[str, Any]) -> int:
        base = int(item.get("score", 0))
        blob = text_blob(item)
        if "工业设计" in blob or "industrial design" in blob:
            base += 12
        if "ai" in blob or "机器人" in blob or "cmf" in blob:
            base += 8
        if item.get("kind") == "article":
            base += 4
        return base

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in sorted(items, key=score, reverse=True):
        key = item.get("url") or item.get("title", "")
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def fallback_article(date: str, index: int, category: str) -> dict[str, Any]:
    titles = {
        "AI硬件": "AI硬件继续从概念展示转向日常使用理由",
        "3C产品": "3C产品设计更关注轻薄形态与可靠触感",
        "清洁电器": "清洁电器竞争点从性能参数转向维护体验",
        "机器人": "机器人产品需要更清晰的状态表达和家庭化语言",
        "CMF": "CMF 趋势继续强调低饱和色、微纹理和触感层次",
    }
    title = titles.get(category, "工业设计作品集需要更明确的设计判断")
    return {
        "id": stable_id(date, "fallback-news", f"{category}-{index}"),
        "title": title,
        "summary": "今日公开信息源抓取不完整，先用备用趋势框架维持日报结构，后续真实来源恢复后会自动替换。",
        "source": "Fallback Rule",
        "category": category,
        "url": "https://github.com/iron2002-xtc/industrial-design-intelligence-mvp",
        "date": date,
        "importanceScore": max(72, 88 - index * 4),
        "designInsight": "把它转成作品集时，重点说明用户场景、结构约束、CMF 取舍和为什么值得做。",
        "keywords": [category, "工业设计", "作品集", "备用数据"],
    }


def to_news_item(item: dict[str, Any], date: str, index: int, kind: str = "news") -> dict[str, Any]:
    category = choose_category(item)
    source = str(item.get("source") or "Public Source")
    raw_title = clean_text(item.get("title"), 90)
    if raw_title and has_cjk(raw_title):
        title = raw_title
    elif raw_title:
        title = f"{source}：{category}相关公开案例值得跟进"
    else:
        title = fallback_article(date, index, category)["title"]

    raw_summary = clean_text(item.get("summary"), 150)
    if raw_summary and has_cjk(raw_summary):
        summary = raw_summary
    elif raw_summary:
        summary = f"公开来源提到“{raw_title or source}”。这条信息可作为 {category} 方向的案例或趋势素材。"
    else:
        summary = "公开来源出现了与工业设计、硬件产品或设计工具相关的新信号。"
    score = min(98, max(70, int(item.get("score", 0)) + 72 - index * 3))
    why = {
        "AI硬件": "它会影响你做智能硬件项目时对交互入口、佩戴/携带理由和长期使用价值的判断。",
        "3C产品": "它适合转化为作品集里的形态语言、细节比例和品牌识别分析。",
        "清洁电器": "它能帮助你把清洁电器项目从外观表达推进到维护路径和家庭动线。",
        "机器人": "它提醒作品集要解释状态反馈、安全感和家居亲和力，而不只是机械外形。",
        "CMF": "它能直接补充材质、色彩、工艺和触感策略页。",
        "AI辅助设计工具": "它适合进入作品集生产流程，但要保留你自己的筛选和判断。",
    }.get(category, "它能补充你的趋势判断和作品集研究素材。")
    return {
        "id": stable_id(date, kind, item.get("id") or title),
        "title": title,
        "summary": summary,
        "source": source,
        "category": category,
        "url": item.get("url") or "https://github.com/iron2002-xtc/industrial-design-intelligence-mvp",
        "date": date,
        "importanceScore": score,
        "designInsight": why,
        "keywords": [category, source, *item.get("keywords", [])][:12],
    }


def build_news(items: list[dict[str, Any]], date: str) -> list[dict[str, Any]]:
    articles = [item for item in sort_items(items) if item.get("kind") == "article"]
    news = [to_news_item(item, date, index + 1, "news") for index, item in enumerate(articles[:5])]
    fallback_categories = ["AI硬件", "3C产品", "清洁电器", "机器人", "CMF"]
    while len(news) < 5:
        news.append(fallback_article(date, len(news) + 1, fallback_categories[len(news) % len(fallback_categories)]))
    return news[:5]


def build_ai_tools(items: list[dict[str, Any]], date: str) -> list[dict[str, Any]]:
    candidates = [
        item
        for item in sort_items(items)
        if any(keyword in text_blob(item) for keyword in ["ai design", "design tool", "生成式", "workflow", "工具"])
    ]
    result = [to_news_item(item, date, index + 1, "tool") for index, item in enumerate(candidates[:3])]
    templates = [
        ("AI辅助调研卡片流程", "把公开来源中的标题、摘要和岗位关键词先整理成研究卡片，再决定作品集页面结构。"),
        ("CMF moodboard 初筛", "AI 可以帮助快速发散材质方向，但最终要由设计师判断工艺可行性和品牌气质。"),
        ("作品集版式检查", "用 AI 检查标题长度、信息层级和页面逻辑，避免项目页只有视觉没有判断。"),
    ]
    while len(result) < 3:
        title, summary = templates[len(result)]
        result.append(
            {
                "id": stable_id(date, "tool", title),
                "title": title,
                "summary": summary,
                "source": "Fallback Rule",
                "category": "AI辅助设计工具",
                "url": "https://github.com/iron2002-xtc/industrial-design-intelligence-mvp",
                "date": date,
                "importanceScore": 82 - len(result) * 3,
                "designInsight": "把工具放在流程里，而不是让工具替代你的设计判断。",
                "keywords": ["AI辅助设计工具", "作品集", "工业设计"],
            }
        )
    return result


def build_hardware_observation(items: list[dict[str, Any]], date: str) -> list[dict[str, Any]]:
    categories = ["智能硬件", "机器人", "清洁电器"]
    result: list[dict[str, Any]] = []
    for category in categories:
        matched = next((item for item in sort_items(items) if category in choose_category(item) or category in text_blob(item)), None)
        if matched:
            result.append(to_news_item(matched, date, len(result) + 1, "hardware"))
        else:
            fallback = fallback_article(date, len(result) + 1, category)
            fallback["id"] = stable_id(date, "hardware", category)
            result.append(fallback)
    return result


def build_trends(items: list[dict[str, Any]], date: str) -> list[dict[str, Any]]:
    sorted_source = sort_items(items)
    trends: list[dict[str, Any]] = []
    for index, category in enumerate(TREND_CATEGORIES):
        keywords = CATEGORY_KEYWORDS.get(category, [])
        matched = next((item for item in sorted_source if any(keyword.lower() in text_blob(item) for keyword in keywords)), None)
        if matched:
            raw_title = clean_text(matched.get("title"), 46)
            title_seed = raw_title if has_cjk(raw_title) else f"{matched.get('source', '公开来源')}新案例"
            raw_summary = clean_text(matched.get("summary"), 160)
            if raw_summary and has_cjk(raw_summary):
                summary = raw_summary
            elif raw_summary:
                summary = f"公开来源提到“{raw_title}”。可作为 {category} 的案例线索，后续适合补充图片、产品语境和设计判断。"
            else:
                summary = f"{category} 出现新的公开信息，值得纳入今日设计研究。"
            url = matched.get("url")
            related = [matched.get("source", "Public Source")]
        else:
            title_seed = category
            summary = f"{category} 今日真实来源不足，先保留趋势观察框架，等待后续自动更新补齐。"
            url = "https://github.com/iron2002-xtc/industrial-design-intelligence-mvp"
            related = ["Fallback Rule"]

        trends.append(
            {
                "id": stable_id(date, "trend", category),
                "title": f"{category}观察：{title_seed}",
                "trendSummary": summary,
                "relatedCases": [*related, "DJI 大疆", "小米"][:3],
                "designInspiration": "把这条趋势拆成用户场景、形态约束、CMF策略和交互入口，转成作品集中的研究页或竞品矩阵。",
                "category": category,
                "url": url,
                "date": date,
                "keywords": [category, *keywords[:5]],
            }
        )
    return trends


def build_jobs(items: list[dict[str, Any]], date: str) -> list[dict[str, Any]]:
    job_pages = [item for item in items if item.get("kind") == "job_page"]
    by_company = {item.get("company"): item for item in job_pages}
    jobs: list[dict[str, Any]] = []

    for index, (company, city, direction, experience, url) in enumerate(TARGET_COMPANY_FALLBACKS):
        source_item = by_company.get(company, {})
        checked = source_item.get("status") == "checked"
        match_score = min(98, 78 + (index * 7) % 16 + (8 if city in {"深圳", "上海", "苏州"} else 3) + (4 if checked else 0))
        job_title = {
            "CMF": "CMF / 工业设计机会跟踪",
            "清洁电器": "清洁电器工业设计机会跟踪",
            "机器人": "机器人产品设计机会跟踪",
            "家电": "家电产品设计机会跟踪",
        }.get(direction, "工业设计 / 产品设计机会跟踪")
        reason_prefix = "官网招聘入口已检查" if checked else "官网岗位页今日解析不稳定，先保留官方入口"
        jobs.append(
            {
                "id": stable_id(date, "job", company),
                "company": company,
                "title": job_title,
                "city": city,
                "direction": direction,
                "experience": source_item.get("experience") or experience,
                "matchScore": match_score,
                "reason": f"{reason_prefix}。该方向与你关注的 {direction}、作品集和秋招准备相关，建议点原始链接核对最新岗位。",
                "url": source_item.get("url") or url,
                "date": date,
                "keywords": [company, city, direction, "工业设计", "招聘", "作品集", "秋招"],
            }
        )

    return sorted(jobs, key=lambda item: item["matchScore"], reverse=True)


def build_actions(report: dict[str, Any]) -> list[dict[str, Any]]:
    top_job = max(report["jobs"], key=lambda item: item["matchScore"])
    top_trend = report["trends"][0]
    return [
        {
            "id": stable_id(report["date"], "action", "portfolio"),
            "title": "作品集优先动作",
            "description": f"把今天的“{top_trend['category']}”趋势转成一页作品集研究卡：场景、竞品、设计判断、可落地方向。",
            "priority": "high",
            "keywords": ["作品集", top_trend["category"], "设计研究"],
        },
        {
            "id": stable_id(report["date"], "action", "jobs"),
            "title": "秋招投递动作",
            "description": f"优先核对 {top_job['company']} 的原始招聘链接，并把岗位关键词补到作品集项目首页。",
            "priority": "medium",
            "keywords": ["秋招", top_job["company"], top_job["city"], top_job["direction"]],
        },
        {
            "id": stable_id(report["date"], "action", "xiaohongshu"),
            "title": "小红书内容动作",
            "description": "把今日 1 条新闻和 1 条趋势拆成 6 图笔记：信号、案例、问题、设计启发、作品集用法、岗位关联。",
            "priority": "low",
            "keywords": ["小红书", "工业设计账号", "内容运营"],
        },
    ]


def clone_previous_as_fallback(previous_report: dict[str, Any], date: str, generated_at: str, message: str) -> dict[str, Any]:
    report = copy.deepcopy(previous_report)
    report["date"] = date
    report["title"] = f"{date} 工业设计早报"
    report["summary"] = "今日部分数据抓取失败，已使用备用数据。"
    report["generatedAt"] = generated_at
    report["dataMode"] = "Fallback"
    report["collectionStatus"] = "fallback"
    report["statusMessage"] = message
    for section in ["topNews", "aiTools", "hardwareObservation", "trends", "jobs"]:
        for index, item in enumerate(report.get(section, [])):
            item["date"] = date
            item["id"] = stable_id(date, section, item.get("id", str(index)))
            if item.get("source") == "Fallback Rule":
                continue
            if section != "jobs":
                item["source"] = f"{item.get('source', '历史数据')} / 备用"
    report["actions"] = build_actions(report)
    report["totalItems"] = total_items(report)
    return report


def total_items(report: dict[str, Any]) -> int:
    return sum(len(report.get(key, [])) for key in ["topNews", "trends", "aiTools", "hardwareObservation", "jobs", "actions"])


def try_openai_refine(report: dict[str, Any], collected_items: list[dict[str, Any]]) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return report

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        compact_sources = [
            {
                "title": item.get("title"),
                "summary": item.get("summary"),
                "source": item.get("source"),
                "category": item.get("category"),
            }
            for item in collected_items[:18]
        ]
        prompt = {
            "task": "请基于公开来源，为工业设计学生生成一句中文日报总结和三条行动建议，保持简洁，有设计判断。",
            "currentSummary": report["summary"],
            "sources": compact_sources,
        }
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            input=json.dumps(prompt, ensure_ascii=False),
        )
        text = getattr(response, "output_text", "") or ""
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return report
        refined = json.loads(match.group(0))
        if isinstance(refined.get("summary"), str):
            report["summary"] = clean_text(refined["summary"], 180)
        if isinstance(refined.get("actions"), list):
            for index, action_text in enumerate(refined["actions"][:3]):
                if isinstance(action_text, str) and index < len(report["actions"]):
                    report["actions"][index]["description"] = clean_text(action_text, 180)
        return report
    except Exception as exc:  # noqa: BLE001 - optional refinement must never break the update.
        report["statusMessage"] = f"{report.get('statusMessage', '')} OpenAI 摘要失败，已使用规则摘要。".strip()
        return report


def build_daily_report(
    collected: dict[str, Any],
    date: str,
    generated_at: str,
    previous_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    items = collected.get("items", [])
    status = collected.get("status", "fallback")
    article_count = len([item for item in items if item.get("kind") in {"article", "search_result"}])
    has_enough_content = article_count >= 3 and len(items) >= 8
    status_message = ""

    if not has_enough_content and previous_report:
        return clone_previous_as_fallback(
            previous_report,
            date,
            generated_at,
            "今日部分数据抓取失败，已使用备用数据。",
        )

    data_mode = "Real" if has_enough_content else "Fallback"
    if data_mode == "Fallback" or status == "partial":
        status_message = "今日部分数据抓取失败，已使用备用数据。"

    report = {
        "date": date,
        "title": f"{date} 工业设计早报",
        "summary": "今日聚焦工业设计、AI硬件、3C、清洁电器、机器人、CMF 与国内岗位机会。",
        "generatedAt": generated_at,
        "sourceCount": int(collected.get("sourceCount", 0)),
        "totalItems": 0,
        "dataMode": data_mode,
        "collectionStatus": status if data_mode == "Real" and status in {"success", "partial"} else ("partial" if items else "fallback"),
        "statusMessage": status_message,
        "topNews": build_news(items, date),
        "trends": build_trends(items, date),
        "aiTools": build_ai_tools(items, date),
        "hardwareObservation": build_hardware_observation(items, date),
        "jobs": build_jobs(items, date),
        "actions": [],
    }
    report["actions"] = build_actions(report)
    report["totalItems"] = total_items(report)
    report["summary"] = f"{report['topNews'][0]['title']}；{report['trends'][0]['category']}趋势值得跟进；{report['jobs'][0]['company']} 等岗位建议核对原始链接。"
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
