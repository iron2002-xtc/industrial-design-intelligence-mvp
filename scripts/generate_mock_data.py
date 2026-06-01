#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIRS = [ROOT / "data", ROOT / "public" / "data"]

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

SOURCE_POOL = ["36氪", "DesignWanted", "小红书趋势", "公司招聘站", "站酷", "机器之心"]

DAY_SEEDS = [
    {
        "date": "2026-06-01",
        "focus": "AI硬件从概念验证转向随身场景",
        "tension": "轻量交互、佩戴舒适度与长期使用理由",
        "citySignal": "深圳、上海、杭州岗位密度最高",
        "portfolioAngle": "用一页讲清楚产品判断和设计取舍",
        "platformSignal": "小红书工业设计内容更适合拆成趋势观察和作品集复盘",
        "actions": [
            "把作品集首页改成 1 个清晰项目定位句 + 3 个设计判断标签。",
            "整理一组 AI 硬件佩戴/桌面场景竞品，补充交互入口和 CMF 对比。",
            "筛出 90+ 匹配岗位，优先投递深圳与上海的智能硬件/机器人方向。",
        ],
    },
    {
        "date": "2026-05-31",
        "focus": "清洁电器开始强调全屋协同体验",
        "tension": "基站体积、维护路径和家庭动线的平衡",
        "citySignal": "苏州、深圳清洁电器岗位活跃",
        "portfolioAngle": "把功能堆叠改写成场景闭环",
        "platformSignal": "短视频更适合展示结构拆解和使用前后对比",
        "actions": [
            "补一张清洁机器人维护路径图，突出用户少弯腰、少接触污水。",
            "把云鲸、追觅、石头科技岗位加入投递清单，并记录岗位关键词。",
            "更新小红书选题：一条讲基站形态，一条讲产品爆炸图表达。",
        ],
    },
    {
        "date": "2026-05-30",
        "focus": "3C产品回到克制、薄型化和可靠触感",
        "tension": "极简外观与高频交互反馈之间的关系",
        "citySignal": "深圳、广州 3C 与 CMF 岗位同时上升",
        "portfolioAngle": "减少大段解释，增加细节特写和材质理由",
        "platformSignal": "账号内容可以从 CMF 趋势切入招聘作品集话题",
        "actions": [
            "重排作品集 CMF 页，把材质策略、色彩角色和触点体验分开讲。",
            "搜集 OPPO、vivo、小米近期产品图，做一页边角、分缝、按键语言对比。",
            "给小红书准备 6 张图的 CMF 复盘模板。",
        ],
    },
    {
        "date": "2026-05-29",
        "focus": "机器人产品的家庭化表达继续增强",
        "tension": "机械可信度与家居亲和力的视觉冲突",
        "citySignal": "杭州、南京机器人与智能硬件岗位更值得看",
        "portfolioAngle": "用场景地图解释形态为什么变柔和",
        "platformSignal": "设计拆解内容需要更明确的观众收益点",
        "actions": [
            "为机器人项目补一张家庭场景触点图，标出声音、灯效、姿态反馈。",
            "投递杭州/南京机器人岗位前，准备 30 秒项目口述版本。",
            "发布一条机器人家庭化趋势卡片，重点讲材质、姿态和灯语。",
        ],
    },
    {
        "date": "2026-05-28",
        "focus": "家电产品把智能化藏进更安静的界面",
        "tension": "屏幕、旋钮、灯效和物理反馈的取舍",
        "citySignal": "广州、上海家电与 CMF 岗位稳定",
        "portfolioAngle": "把交互层级画成可读的状态系统",
        "platformSignal": "家电趋势内容适合用 before/after 视觉对照",
        "actions": [
            "整理美的、海尔、TCL 的控制面板语言，提炼 3 个设计原则。",
            "作品集里补一个状态流：待机、运行、异常、维护。",
            "把家电项目的 UI 文字缩短，保留最关键的状态和动作。",
        ],
    },
    {
        "date": "2026-05-27",
        "focus": "AI设计工具进入作品集生产链路",
        "tension": "效率提升与原创判断的边界",
        "citySignal": "上海、深圳更偏 AI 工具和智能硬件交叉岗位",
        "portfolioAngle": "明确哪些是 AI 辅助，哪些是自己的设计判断",
        "platformSignal": "账号可以用工具流复盘吸引同专业学生",
        "actions": [
            "建立一个 AI 辅助设计流程页：调研、草图、CMF、版面，不写成炫技。",
            "把作品集里的 AI 生成图标注为辅助素材，保留自己选择理由。",
            "准备一条小红书：3 个工具如何帮工业设计作品集提速。",
        ],
    },
    {
        "date": "2026-05-26",
        "focus": "秋招工业设计岗位更看重完整项目叙事",
        "tension": "从单张效果图转向问题定义、过程和落地表达",
        "citySignal": "深圳、苏州、上海岗位池更适合优先跟进",
        "portfolioAngle": "用项目首页承担招聘筛选的第一印象",
        "platformSignal": "求职内容可以拆成岗位分析、作品集页改造和面试表达",
        "actions": [
            "挑 2 个最强项目做一页式项目摘要，先服务秋招筛选。",
            "建立岗位关键词表：城市、方向、软件、经验、加分项。",
            "小红书账号本周先发求职向内容，不急着做复杂教程。",
        ],
    },
]

JOB_POOL = [
    ("DJI 大疆", "工业设计实习生", "深圳", "智能硬件", "实习 / 校招", "硬件产品线完整，适合展示结构理解、CMF 判断和高质量建模表达。", "https://www.dji.com/cn/careers", ["大疆", "DJI", "深圳", "智能硬件", "工业设计", "作品集"]),
    ("华为", "终端工业设计师", "深圳", "3C", "校招 / 0-2 年", "手机、穿戴、智慧屏方向与 3C 产品审美和系统级体验表达高度相关。", "https://career.huawei.com/reccampportal/portal5/index.html", ["华为", "深圳", "3C", "终端", "穿戴", "CMF"]),
    ("小米", "智能硬件工业设计师", "上海", "智能硬件", "校招 / 1-3 年", "产品覆盖 IoT 与生活方式硬件，适合用系统化项目叙事打动筛选者。", "https://hr.xiaomi.com/", ["小米", "上海", "IoT", "智能硬件", "生态链"]),
    ("OPPO", "CMF 设计实习生", "深圳", "CMF", "实习", "适合用材质趋势、色彩策略、工艺边界和触感样本提升作品集辨识度。", "https://careers.oppo.com/", ["OPPO", "深圳", "CMF", "色彩", "材料", "工艺"]),
    ("vivo", "手机工业设计师", "深圳", "3C", "校招", "与 3C 形态、握持、边角语言、镜头模组设计表达高度匹配。", "https://hr.vivo.com/", ["vivo", "深圳", "3C", "手机", "工业设计"]),
    ("Insta360 影石", "运动影像产品设计师", "深圳", "3C", "1-3 年", "影像设备强调便携、模块化和户外可靠性，适合展示细节推敲能力。", "https://www.insta360.com/cn/careers", ["影石", "Insta360", "深圳", "相机", "3C", "运动影像"]),
    ("云鲸", "清洁机器人工业设计师", "深圳", "清洁电器", "校招 / 1-3 年", "与你关注的清洁电器和机器人高度重合，可用场景闭环和基站体验切入。", "https://www.narwal.com/cn/careers", ["云鲸", "深圳", "清洁电器", "机器人", "基站"]),
    ("追觅", "产品设计师 - 清洁电器", "苏州", "清洁电器", "校招 / 1-3 年", "品类与作品集方向匹配，重点准备结构爆炸、维护动线和 CMF 说明。", "https://www.dreame.tech/cn/careers", ["追觅", "苏州", "清洁电器", "扫地机", "洗地机"]),
    ("石头科技", "机器人产品工业设计", "上海", "机器人", "1-3 年", "清洁机器人与家庭服务机器人经验可迁移，适合强调落地和可靠性。", "https://cn.roborock.com/pages/join-us", ["石头科技", "上海", "机器人", "清洁电器", "工业设计"]),
    ("TCL", "家电工业设计师", "广州", "家电", "校招", "适合展示家电控制界面、CMF 家居化和多产品系列语言。", "https://campus.tcl.com/", ["TCL", "广州", "家电", "工业设计", "CMF"]),
    ("美的", "生活电器产品设计师", "广州", "家电", "校招 / 1-3 年", "家电品类丰富，作品集可突出人机交互、状态反馈和家庭场景洞察。", "https://careers.midea.com/", ["美的", "广州", "家电", "生活电器", "交互"]),
    ("科沃斯", "服务机器人设计师", "苏州", "机器人", "校招 / 1-3 年", "机器人方向明确，适合用服务场景、灯语、结构维护和产品家居化表达。", "https://www.ecovacs.cn/careers", ["科沃斯", "苏州", "机器人", "服务机器人", "清洁"]),
    ("海尔", "智慧家电 CMF 设计", "南京", "CMF", "校招", "适合把材质、色彩与家居环境结合，补足作品集的趋势判断层。", "https://maker.haier.net/client/join", ["海尔", "南京", "家电", "CMF", "智慧家庭"]),
    ("宇树科技", "机器人外观设计师", "杭州", "机器人", "校招 / 1-3 年", "机器人硬件辨识度强，适合展示机械结构理解和未来感形态控制。", "https://www.unitree.com/cn/about/careers", ["宇树", "杭州", "机器人", "外观设计", "智能硬件"]),
]


def news(seed: dict[str, Any], day_index: int) -> list[dict[str, Any]]:
    templates = [
        ("AI硬件", f"{seed['focus']}，产品团队开始重写使用理由", f"从概念展示转向日常入口，核心矛盾集中在 {seed['tension']}。", "作品集不只放效果图，要说明为什么用户会持续佩戴、拿起或复用这个产品。", ["AI硬件", "智能硬件", "使用理由", "交互入口"]),
        ("秋招", f"{seed['citySignal']}，工业设计岗位更偏复合型表达", "招聘描述里频繁出现结构理解、CMF、渲染表现、用户洞察和跨团队沟通。", "投递前把项目页的前 20 秒阅读体验做好，先让 HR 和设计面试官看懂方向。", ["秋招", "岗位", "城市", "作品集", "工业设计"]),
        ("清洁电器", "清洁电器从吸力参数转向维护体验和家居融合", "基站、耗材、污水路径和收纳体积成为用户评价里更具体的痛点。", "可以把维护流程画成信息图，比单纯展示外观更能体现工业设计价值。", ["清洁电器", "基站", "维护", "家居", "机器人"]),
        ("CMF", "CMF 语言继续向低饱和、细纹理和触感层次收敛", "高端产品不再只靠亮面金属，更多用微纹理、消光、亲肤和隐藏分缝建立品质感。", "把 CMF 写成策略：使用场景、耐脏要求、触点优先级和品牌气质。", ["CMF", "材料", "工艺", "触感", "高级灰"]),
        ("小红书运营", seed["platformSignal"], "设计账号更容易被收藏的内容，通常是可复用模板、竞品拆解和求职路径图。", "把一条长内容拆成 6 张图：趋势信号、案例、设计判断、作品集启发、岗位关键词、行动清单。", ["小红书", "账号运营", "工业设计", "内容", "作品集"]),
    ]

    return [
        {
            "id": f"{seed['date']}-news-{index + 1}",
            "title": title,
            "summary": summary,
            "source": SOURCE_POOL[(day_index + index) % len(SOURCE_POOL)],
            "category": category,
            "url": f"https://example.com/industrial-design/news/{seed['date']}-{index + 1}",
            "date": seed["date"],
            "importanceScore": 95 - index * 4 - (day_index % 2),
            "designInsight": insight,
            "keywords": [seed["focus"], seed["tension"], seed["portfolioAngle"], *keywords],
        }
        for index, (category, title, summary, insight, keywords) in enumerate(templates)
    ]


def trends(seed: dict[str, Any]) -> list[dict[str, Any]]:
    summaries = {
        "AI硬件": f"AI硬件的重点从“能不能做”转向“用户为什么每天愿意用”，{seed['tension']} 是筛选好概念的关键。",
        "3C产品": "3C产品继续收紧视觉噪音，镜头模组、边框、按键和握持区域成为品牌识别重点。",
        "清洁电器": "清洁电器的竞争点转向维护路径、基站尺度和家庭空间协调，而不是单一性能数字。",
        "机器人": "家庭机器人需要降低机械压迫感，用灯语、姿态和材质让用户快速理解状态。",
        "家电": "家电界面从大屏炫技回到安静反馈，旋钮、灯带和小面积屏幕形成更稳的状态系统。",
        "CMF": "低饱和色、微纹理、亲肤涂层和可持续材料会继续出现在高端硬件语言里。",
        "AI辅助设计工具": "AI工具适合作为调研、草图、版式和 CMF moodboard 的辅助链路，但需要保留设计师判断。",
        "工业设计作品集案例": f"{seed['portfolioAngle']}，让项目第一页承担“问题、机会、方案价值”的快速筛选。",
    }

    return [
        {
            "id": f"{seed['date']}-trend-{index + 1}",
            "title": f"{category}观察：{seed['focus'] if index % 2 == 0 else seed['portfolioAngle']}",
            "trendSummary": summaries[category],
            "relatedCases": [
                ["大疆", "华为", "小米", "OPPO"][index % 4],
                ["云鲸", "追觅", "石头科技", "科沃斯"][index % 4],
                ["Insta360", "TCL", "美的", "海尔"][index % 4],
            ],
            "designInspiration": "把趋势拆成用户场景、形态约束、CMF策略和交互入口，形成作品集可展示的一页。" if index % 2 == 0 else "用竞品矩阵记录品牌语言差异，避免只做审美描述。",
            "category": category,
            "url": f"https://example.com/industrial-design/trends/{seed['date']}-{index + 1}",
            "date": seed["date"],
            "keywords": [category, seed["focus"], seed["tension"], seed["portfolioAngle"], seed["citySignal"]],
        }
        for index, category in enumerate(TREND_CATEGORIES)
    ]


def ai_tools(seed: dict[str, Any]) -> list[dict[str, Any]]:
    items = [
        ("AI 辅助调研卡片生成流程", "把招聘关键词、竞品观察和用户痛点先整理成结构化卡片，再进入版面设计。", "适合做每天自动更新后的第一层摘要，不直接替代你的设计判断。", ["AI工具", "调研", "卡片", "自动摘要"]),
        ("CMF moodboard 的 AI 初筛用法", "先让 AI 生成材质方向，再由设计师筛掉不符合工艺、品牌和触感的部分。", "作品集中要写清楚选择理由，避免变成单纯拼贴。", ["AI辅助设计工具", "CMF", "moodboard", "材质"]),
        ("作品集版式检查清单", "用 AI 检查信息层级、标题长度和页面逻辑，再手动做视觉节奏调整。", "最适合检查“能不能 20 秒看懂”，不适合替你定最终风格。", ["作品集", "版式", "AI设计", "检查清单"]),
    ]

    return [
        {
            "id": f"{seed['date']}-tool-{index + 1}",
            "title": title,
            "summary": summary,
            "source": "AI Design Workflow",
            "category": "AI设计与工具",
            "url": f"https://example.com/industrial-design/ai-tools/{seed['date']}-{index + 1}",
            "date": seed["date"],
            "importanceScore": 88 - index * 3,
            "designInsight": insight,
            "keywords": [seed["focus"], *keywords],
        }
        for index, (title, summary, insight, keywords) in enumerate(items)
    ]


def hardware_observation(seed: dict[str, Any]) -> list[dict[str, Any]]:
    items = [
        ("智能硬件观察：入口小型化，体验系统化", f"产品形态变轻，但背后的服务链路更长，设计要处理 {seed['tension']}。", "适合用服务蓝图把硬件、App、配件和售后维护串起来。", "智能硬件", ["智能硬件", "服务链路", "体验系统"]),
        ("机器人观察：状态表达比拟人外观更重要", "家庭场景里，用户更需要知道机器人在做什么、是否安全、何时需要干预。", "灯语、声音和姿态反馈可以成为作品集里的交互亮点。", "机器人", ["机器人", "灯语", "状态反馈", "家庭场景"]),
        ("清洁电器观察：基站是新的产品主角", "基站负责收纳、补水、清洗、烘干和污水处理，决定产品是否真正省心。", "基站体积、开盖方向和耗材路径很适合画成结构体验图。", "清洁电器", ["清洁电器", "基站", "维护路径", "结构"]),
    ]

    return [
        {
            "id": f"{seed['date']}-hardware-{index + 1}",
            "title": title,
            "summary": summary,
            "source": "Hardware Watch",
            "category": category,
            "url": f"https://example.com/industrial-design/hardware/{seed['date']}-{index + 1}",
            "date": seed["date"],
            "importanceScore": 91 - index * 4,
            "designInsight": insight,
            "keywords": [seed["focus"], seed["citySignal"], *keywords],
        }
        for index, (title, summary, insight, category, keywords) in enumerate(items)
    ]


def jobs(seed: dict[str, Any], day_index: int) -> list[dict[str, Any]]:
    result = []
    for index, (company, title, city, direction, experience, reason, url, keywords) in enumerate(JOB_POOL):
        delta = ((day_index + index) % 5) * 2
        city_boost = 4 if city in seed["citySignal"] else 0
        direction_boost = 3 if direction in seed["focus"] else 0
        base = 78 + ((index * 7 + day_index * 3) % 18)
        match_score = min(99, base + city_boost + direction_boost - delta)
        result.append(
            {
                "id": f"{seed['date']}-job-{index + 1}",
                "company": company,
                "title": title,
                "city": city,
                "direction": direction,
                "experience": experience,
                "matchScore": match_score,
                "reason": f"{reason} 今日信号：{seed['citySignal']}；建议作品集重点回应“{seed['portfolioAngle']}”。",
                "url": url,
                "date": seed["date"],
                "keywords": keywords,
            }
        )
    return result


def actions(seed: dict[str, Any]) -> list[dict[str, Any]]:
    priorities = ["high", "medium", "low"]
    titles = ["作品集优先动作", "趋势素材动作", "秋招投递动作"]
    return [
        {
            "id": f"{seed['date']}-action-{index + 1}",
            "title": titles[index],
            "description": description,
            "priority": priorities[index],
            "keywords": ["行动建议", "作品集", "秋招", "小红书", seed["portfolioAngle"]],
        }
        for index, description in enumerate(seed["actions"])
    ]


def build_report(seed: dict[str, Any], day_index: int) -> dict[str, Any]:
    report = {
        "date": seed["date"],
        "title": f"{seed['date']} 工业设计早报",
        "summary": f"{seed['focus']}；{seed['citySignal']}；作品集重点：{seed['portfolioAngle']}。",
        "generatedAt": f"{seed['date']}T08:30:00+08:00",
        "sourceCount": 0,
        "totalItems": 0,
        "topNews": news(seed, day_index),
        "trends": trends(seed),
        "aiTools": ai_tools(seed),
        "hardwareObservation": hardware_observation(seed),
        "jobs": jobs(seed, day_index),
        "actions": actions(seed),
    }
    source_names = {
        item["source"]
        for item in [*report["topNews"], *report["aiTools"], *report["hardwareObservation"]]
    }
    source_names.update(["目标公司招聘页", "设计趋势观察", "作品集运营记录"])
    report["sourceCount"] = len(source_names)
    report["totalItems"] = sum(
        len(report[key])
        for key in ["topNews", "trends", "aiTools", "hardwareObservation", "jobs", "actions"]
    )
    return report


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clear_reports_dir(base_dir: Path) -> None:
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    for old_report in reports_dir.glob("*.json"):
        old_report.unlink()


def main() -> None:
    reports = [build_report(seed, index) for index, seed in enumerate(DAY_SEEDS)]
    reports.sort(key=lambda item: item["date"], reverse=True)
    latest = reports[0]
    index = [
        {
            "date": report["date"],
            "title": report["title"],
            "summary": report["summary"],
            "newsCount": len(report["topNews"]),
            "jobsCount": len(report["jobs"]),
            "trendsCount": len(report["trends"]),
            "highMatchJobsCount": len([job for job in report["jobs"] if job["matchScore"] >= 90]),
        }
        for report in reports
    ]

    for data_dir in DATA_DIRS:
        clear_reports_dir(data_dir)
        write_json(data_dir / "latest.json", latest)
        write_json(data_dir / "reportsIndex.json", index)
        for report in reports:
            write_json(data_dir / "reports" / f"{report['date']}.json", report)

    print(f"Generated {len(reports)} mock reports.")
    print(f"Latest report: {latest['date']}")
    print("Updated data/ and public/data/ for static frontend delivery.")


if __name__ == "__main__":
    main()
