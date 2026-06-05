# 工业设计求职与设计热点日报最终验收报告

验收日期：2026-06-05  
项目：industrial-design-intelligence-mvp  
公网地址：https://iron2002-xtc.github.io/industrial-design-intelligence-mvp/

## 1. 验收结论

项目已成功部署到 GitHub Pages，公网页面可访问，公网 `latest.json` 已更新为本次岗位详情复核与热点质量过滤后的数据结构。

本次验收结论：通过。

## 2. 仓库与部署状态

- 当前分支：`main`
- Git 状态：`main...origin/main`，本地与远端同步
- 最新提交：`2c406e6 Tighten job detail verification and hotspot quality`
- GitHub Actions：
  - Workflow：`Deploy to GitHub Pages`
  - 触发方式：`push`
  - 状态：`completed / success`
- GitHub Pages：
  - 公网页面返回：`HTTP/2 200`
  - 最近部署时间对应页面 `last-modified`：2026-06-05

## 3. 公网 latest.json 验收结果

公网数据文件：
https://iron2002-xtc.github.io/industrial-design-intelligence-mvp/data/latest.json

当前日报：

- `date`: `2026-06-05`
- `title`: `2026-06-05 工业设计求职与设计热点日报`
- `dataMode`: `Fallback`
- `collectionStatus`: `fallback`
- `sourceCount`: `24`
- `totalItems`: `14`

岗位质量数据：

- `verifiedJobsCount`: `1`
- `likelyJobsCount`: `0`
- `unverifiedJobsCount`: `0`
- `fallbackJobsCount`: `0`
- `highMatchVerifiedJobsCount`: `1`
- `highMatchJobsCount`: `1`
- `verifiedJobDetailsChecked`: `3`
- `verifiedJobsDowngraded`: `2`
- `jobDetailPagesPassed`: `1`
- `jobDetailPagesFailed`: `0`

热点质量数据：

- `totalCollected`: `84`
- `afterDedup`: `84`
- `afterQualityFilter`: `9`
- `genericHotspotsFiltered`: `73`
- `concreteHotspotsKept`: `7`

## 4. 当前核心能力

### 4.1 岗位抓取与筛选

系统已配置目标公司官网招聘源，并从公开页面中提取岗位线索。当前可识别公司官网、招聘平台、搜索结果和备用数据来源，并将岗位进入统一数据结构。

当前已验证岗位：

- 公司：小米
- 岗位：工业设计师
- 城市：北京
- 方向：智能硬件
- 状态：`verified`
- 来源类型：`official`
- 匹配分：`99`
- 可信度：`95`
- 原始链接：https://hr.xiaomi.com/job/view/129

### 4.2 岗位真实性分类

系统支持以下岗位真实性分层：

- `verified`：官网或官方招聘系统中的具体岗位详情页，且能提取岗位名称、城市、职责或要求、强相关设计关键词。
- `likely`：可信招聘平台或可打开的岗位详情页，信息较完整但不满足官网 verified 标准。
- `unverified`：搜索结果或无法完整确认详情的岗位线索，不进入高匹配岗位。
- `fallback`：备用数据，不进入高匹配岗位。

### 4.3 岗位详情复核

系统已增加岗位详情页复核能力，能保存：

- 真实岗位标题
- 工作城市
- 职位类别
- 岗位职责摘要
- 任职要求摘要
- evidenceText
- lastCheckedAt
- sourceType
- confidenceScore

当前小米岗位复核结果：

- 页面为具体岗位详情页。
- 真实标题已从“工业设计 / 产品设计机会跟踪”修正为“工业设计师”。
- 成功提取岗位职责。
- 页面未提供明确任职要求条目，系统已保留“投递前需再次核对”的说明。

### 4.4 高匹配岗位排序

系统已将匹配分与真实性挂钩：

- 高匹配岗位必须满足 `matchScore >= 85`
- `confidenceScore >= 75`
- `verificationStatus` 必须是 `verified` 或 `likely`
- `unverified` 和 `fallback` 不进入高匹配岗位

当前高匹配岗位数：`1`。

### 4.5 设计热点筛选

系统已过滤明显泛泛或误命中的热点标题，例如：

- 搜索结果页
- 早报合集
- 百科页
- 下载页
- 官网首页
- 旅行/3C认证等错类内容
- 泛泛 AI 模型、融资、上市类内容

当前公网保留具体热点数：`7`。

当前保留热点包括：

- WWDC26 开幕在即，今年有哪些看点值得关注？
- 小车车里的大世界：车模收藏入坑指南
- 是时候造一台 AI 时代的手机了｜AIDONE 第五期
- 制糖工厂发布 AI 小电拼 Mirror：FluxAI 自由流让多口充电进入「功率复用」时代
- 云台相机 2026 大乱斗，它到底怎么来的，又去往哪里？｜硬哲学
- 刚刚，Windows「梦中神机」来了，把你的 PC 变成 Agent 工位
- 制糖工厂发布 AI 小电拼 Mirror，支持 AI Agent 原生接入

## 5. 可靠性边界

### 可以相对信任的结果

- `verified` 岗位：可信度最高，可作为优先查看和投递依据。
- 高匹配岗位数量：已受真实性规则约束，不会把普通搜索结果伪装成高匹配岗位。
- `genericHotspotsFiltered`、`concreteHotspotsKept` 等质量指标：可以反映当天过滤力度和保留数量。
- 公司官网抓取状态：可用于判断哪些公司源成功、无匹配或失败。

### 仍需人工复核的结果

- `verified` 岗位仍建议投递前人工打开官网确认是否仍开放。
- 页面未提取到明确任职要求的岗位，需要人工查看原页面补充判断。
- `likely` 岗位只能作为较可信线索，不应直接等同官网岗位。
- 设计热点虽然已过滤泛泛标题，但仍需人工判断其是否适合放入作品集调研。
- `dataMode: Fallback` 或 `collectionStatus: fallback` 表示当天关键源抓取不足，日报仍可看，但应更谨慎解释。

### 当前限制

- 部分公司官网存在反爬、跳转、超时或 404，当前状态会记录为 `blocked_or_failed` 或 `no_matching_jobs`。
- 公开 RSS / 搜索源质量不稳定，设计热点仍可能出现边界案例。
- 系统不会绕过登录、验证码或反爬限制。
- 当前仍是静态前端 + JSON 数据，不包含后端数据库和人工审核后台。

## 6. 本次验收命令摘要

已执行并通过：

- `git status`
- `git log --oneline -5`
- `git remote -v`
- `gh run list --repo iron2002-xtc/industrial-design-intelligence-mvp --limit 5`
- `curl -I -L https://iron2002-xtc.github.io/industrial-design-intelligence-mvp/`
- `curl -L https://iron2002-xtc.github.io/industrial-design-intelligence-mvp/data/latest.json`
- `npm run validate:data`

构建验证在此前推送前已通过：

- `npm run build`
- `GITHUB_PAGES=true npm run build`

## 7. 后续建议

1. 将 `verified` 岗位作为日报里的主投递入口，其他岗位只作为线索。
2. 继续补充更多可直接访问的公司官网岗位详情 URL。
3. 对设计热点增加人工收藏/删除清单，形成半自动审核机制。
4. 后续如接入数据库，可保存岗位状态变化和历史投递记录。
5. 若要进一步提升可信度，可增加每日人工抽样复核步骤。

