# 工业设计求职与设计热点日报

这是一个面向工业设计学生/设计师的日报 Dashboard，当前定位已经收敛为“工业设计求职 + 设计热点”。它每天自动整理工业设计相关岗位、目标公司动态、产品设计热点、CMF、3C、智能硬件、AI硬件、机器人、家电、清洁电器、影像设备、可穿戴和设计奖项案例。

当前版本是半真实自动更新版本：

- `data/`：项目根目录下的 canonical JSON 数据，适合 GitHub Actions 生成并提交。
- `public/data/`：前端静态读取的数据镜像，GitHub Pages 会以 `/data/...` 路径提供。
- `scripts/`：公开来源采集、日报整理、数据校验和 fallback 逻辑。

## 本地运行

如果系统里已有 Node.js 和 npm：

```bash
npm install
npm run dev
```

本机如果没有全局 npm，可以使用项目内置 Node：

```bash
PATH="$PWD/.tools/node/bin:$PATH" npm install
PATH="$PWD/.tools/node/bin:$PATH" npm run dev
```

默认预览地址：

```text
http://127.0.0.1:5173/
```

## 重新生成 mock 数据

Mac：

```bash
npm run generate:mock
```

或直接运行：

```bash
python3 scripts/generate_mock_data.py
```

Windows：

```powershell
py -3 scripts/generate_mock_data.py
```

生成内容包括：

- `data/latest.json`
- `data/reportsIndex.json`
- `data/reports/YYYY-MM-DD.json`
- `public/data/latest.json`
- `public/data/reportsIndex.json`
- `public/data/reports/YYYY-MM-DD.json`

## 手动更新半真实数据

当前版本会优先收集公开 RSS、公开网页、公司官网招聘页和少量公开搜索结果；如果某些来源失败，会记录日志并使用备用数据，保证页面不崩。生成内容只保留求职机会、设计热点、公司动态和作品集/求职行动建议。

先安装 Python 依赖：

```bash
pip install -r requirements.txt
```

手动运行一次更新：

```bash
npm run update:data
```

这个命令会更新：

- `data/latest.json`
- `data/reports/YYYY-MM-DD.json`
- `data/reportsIndex.json`
- `public/data/latest.json`
- `public/data/reports/YYYY-MM-DD.json`
- `public/data/reportsIndex.json`

采集到的原始来源快照会写到 `data/collected/`，该目录已加入 `.gitignore`，不会提交到 Git。

如果想用 AI 优化中文摘要，可以设置环境变量：

```bash
export OPENAI_API_KEY="你的 key"
npm run update:data
```

没有 `OPENAI_API_KEY` 也可以运行，会自动使用规则摘要和备用总结。

## 数据质量与岗位真实性

岗位会同时给出 `matchScore` 和 `confidenceScore`：

- `matchScore`：岗位与目标公司、城市、方向、经验要求的匹配度。
- `confidenceScore`：岗位真实性/来源可信度，越高越说明原始页面更可验证。

岗位真实性字段：

- `verified`：官网或详情页中能看到岗位名称、公司和城市，可作为优先投递对象。
- `likely`：正规招聘平台或可打开详情页中能看到较明确岗位信息，建议重点核对。
- `unverified`：搜索结果或官网入口线索，无法确认完整岗位详情，只放在待核实区。
- `fallback`：备用数据或 mock 补充内容，不作为真实投递依据。

来源类型：

- `official`：公司官网招聘页或官方招聘入口。
- `job_board`：正规招聘平台。
- `search_result`：搜索结果线索。
- `media`：媒体或公开内容。
- `fallback`：备用数据。

高匹配岗位必须同时满足：

```text
matchScore >= 85
confidenceScore >= 75
verificationStatus = verified 或 likely
```

搜索结果来源不能直接进入高匹配岗位。只有当脚本成功打开搜索结果指向的具体详情页，并提取到岗位、公司、城市等证据后，才可能被标记为 `likely`。

匹配分会按真实性系数折算：

- `verified`：乘以 `1.00`
- `likely`：乘以 `0.85`
- `unverified`：乘以 `0.60`
- `fallback`：乘以 `0.45`

并且：

- `unverified` 最高不超过 80 分。
- `fallback` 最高不超过 65 分。
- `fallback` 的 `confidenceScore` 不高于 50。

设计热点也会做质量过滤：

- 不把 Bing/搜索结果页本身当热点。
- 搜索结果必须能打开具体文章、产品或案例页才可能进入日报。
- `relevanceScore < 70` 或 `confidenceScore < 65` 的真实热点会被过滤。
- 宁可热点更少，也不塞泛泛内容。

每日 JSON 中的 `qualityReport` 会记录：

- 收集总数、去重后数量、质量过滤后数量。
- verified / likely / unverified / fallback 岗位数量。
- 官网来源岗位数量。
- 被过滤的泛搜索结果数量。
- 失败来源列表。
- 每家公司官网抓取状态。

新增公司官网招聘源：

1. 打开 `scripts/sources.yaml`。
2. 在 `company_careers` 下新增公司。
3. 填写 `company`、`city`、`direction`、`experience`、`url`、`keywords`。
4. 运行 `npm run update:data`。
5. 运行 `npm run validate:data`。

公司官网抓取状态含义：

- `success`：官网页面可访问，并命中岗位关键词。
- `no_matching_jobs`：官网页面可访问，但没有命中工业设计/产品设计/CMF 等岗位关键词。
- `blocked_or_failed`：官网页面访问失败、超时或被拦截。
- `not_configured`：目标公司暂未配置抓取入口。

## 校验数据

Mac：

```bash
npm run validate:data
```

或直接运行：

```bash
python3 scripts/validate_data.py
```

Windows：

```powershell
py -3 scripts/validate_data.py
```

校验内容：

- `latest.json` 是否存在且 JSON 合法。
- `reportsIndex.json` 是否存在且包含历史日报索引。
- `latest.json` 是否与索引中最新日期一致。
- 每个 report 是否包含 `jobOpportunities`、`highMatchJobs`、`designHotspots`、`companyUpdates`、`actions`。
- `newsCount`、`jobsCount`、`trendsCount`、`highMatchJobsCount` 是否与日报内容一致。
- 日报展示字段中不包含已移除的社交媒体选题内容。

## Build

```bash
npm run build
```

构建产物在 `dist/`。

GitHub Pages 构建会使用仓库子路径：

```bash
GITHUB_PAGES=true npm run build
```

## 数据结构

核心类型在 `src/types/report.ts`。

`DailyReport` 包含：

- `date`
- `title`
- `summary`
- `generatedAt`
- `dataMode`
- `sourceCount`
- `totalItems`
- `qualitySummary`
- `jobOpportunities`
- `highMatchJobs`
- `designHotspots`
- `companyUpdates`
- `actions`

为了兼容历史页面和旧数据，JSON 中可能仍保留 `topNews`、`trends`、`jobs` 等镜像字段，但页面展示以新结构为主。

### 配置位置

城市优先级、目标公司、招聘关键词和设计热点关键词都在：

```text
scripts/sources.yaml
```

修改城市优先级：

- `city_priority.first`
- `city_priority.second`
- `city_priority.third`

修改目标公司：

- `target_companies.domestic`
- `target_companies.global`
- `company_careers`

修改招聘关键词：

- `keywords.job_core`
- `keywords.job_industries`
- `job_search_queries.queries`

修改设计热点关键词：

- `keywords.hotspot_core`
- `hotspot_search_queries.queries`

改完后运行：

```bash
npm run update:data
npm run validate:data
npm run build
```

`ReportIndexItem` 包含：

- `date`
- `title`
- `summary`
- `newsCount`
- `jobsCount`
- `trendsCount`
- `highMatchJobsCount`

## 未来接入真实抓取

下一步可以把 `scripts/generate_mock_data.py` 替换或扩展为真实数据管线：

1. 新增数据源配置，例如设计媒体 RSS、目标公司招聘页、公开岗位聚合页和目标公司产品动态源。
2. 抓取后做清洗、去重、分类、关键词提取和匹配度评分。
3. 生成同样结构的 `DailyReport` JSON。
4. 保留 `validate_data.py` 作为 CI 质量门槛。
5. 用 GitHub Actions 每天定时运行脚本，自动提交 `data/` 和 `public/data/`。

## 部署到 GitHub Pages

这是当前推荐的免费公网访问方案。仓库需要是 public，GitHub Actions 会在每次推送 `main` 后自动构建并发布。

当前公网访问地址：

```text
https://iron2002-xtc.github.io/industrial-design-intelligence-mvp/
```

自动部署流程写在 `.github/workflows/deploy.yml`：

1. `npm ci`
2. `npm run validate:data`
3. `GITHUB_PAGES=true npm run build`
4. 上传 `dist/`
5. 发布到 GitHub Pages

`vite.config.ts` 会在 `GITHUB_PAGES=true` 时把资源路径切到：

```text
/industrial-design-intelligence-mvp/
```

前端读取数据时使用 `import.meta.env.BASE_URL`，因此 GitHub Pages 下会读取：

```text
/industrial-design-intelligence-mvp/data/latest.json
/industrial-design-intelligence-mvp/data/reportsIndex.json
/industrial-design-intelligence-mvp/data/reports/YYYY-MM-DD.json
```

如果部署后页面暂时打不开，通常是 GitHub Actions 还在构建，等 1-3 分钟后刷新即可。

## 每天自动更新

自动更新 workflow 写在 `.github/workflows/daily-update.yml`。

运行时间：

- 每天北京时间 7:30 自动运行。
- 对应 GitHub Actions cron：`30 23 * * *`。
- 支持在 GitHub 页面手动触发 `workflow_dispatch`。

自动流程：

1. 安装 Python 依赖。
2. 安装 Node 依赖。
3. 运行 `npm run update:data`。
4. 运行 `npm run validate:data`。
5. 自动提交 `data/` 和 `public/data/` 中更新后的日报 JSON。
6. 使用 `GITHUB_PAGES=true npm run build` 构建。
7. 发布到 GitHub Pages。

手动触发方式：

1. 打开 GitHub 仓库。
2. 进入 `Actions`。
3. 选择 `Daily Data Update`。
4. 点击 `Run workflow`。
5. 选择 `main` 分支并确认运行。

配置 `OPENAI_API_KEY`：

1. 打开 GitHub 仓库。
2. 进入 `Settings`。
3. 进入 `Secrets and variables` -> `Actions`。
4. 点击 `New repository secret`。
5. Name 填 `OPENAI_API_KEY`。
6. Secret 填你的 OpenAI API key。

这个 key 是可选的。不配置时，自动更新仍会运行，只是使用规则摘要。

查看是否运行成功：

1. 打开仓库 `Actions` 页面。
2. 看 `Daily Data Update` 最近一次运行是否为绿色勾。
3. 如果失败，点进运行记录，看 `Update daily data`、`Validate data` 或 `Build` 哪一步报错。
4. 如果成功，回到仓库首页看最新 commit 是否为 `Update daily industrial design report`。

确认 GitHub Pages 已更新：

1. 打开公网链接：

```text
https://iron2002-xtc.github.io/industrial-design-intelligence-mvp/
```

2. 看页面顶部的 `生成` 时间、`模式`、`来源` 和 `收录` 是否变化。
3. 也可以直接打开：

```text
https://iron2002-xtc.github.io/industrial-design-intelligence-mvp/data/latest.json
```

常见错误排查：

- RSS 或招聘页抓取失败：正常情况，脚本会跳过该来源并使用备用数据。
- 页面显示 `Fallback`：说明真实来源不足或部分抓取失败，页面仍可用。
- GitHub Actions 没有自动提交：可能是当天生成内容与仓库一致，workflow 会正常结束。
- `OPENAI_API_KEY` 报错：删除或更新 GitHub Secret；无 key 时会自动回退到规则摘要。
- GitHub Pages 页面没更新：等待 1-3 分钟，或检查 `Actions` 里的部署是否成功。

## 部署到 Vercel

这一节是从本地项目到手机公网访问的完整路径。

### 1. 上传到 GitHub

先在本地确认已经提交 Git：

```bash
git status
```

然后在 GitHub 新建一个空仓库，例如：

```text
industrial-design-intelligence-mvp
```

不要勾选自动生成 README、`.gitignore` 或 license，因为本地项目已经有这些文件。

把 GitHub 页面给出的远程仓库地址复制下来，然后在本地项目目录执行：

```bash
git remote add origin https://github.com/YOUR_NAME/industrial-design-intelligence-mvp.git
git branch -M main
git push -u origin main
```

如果你使用 SSH 地址，也可以把 `origin` 换成类似：

```bash
git remote add origin git@github.com:YOUR_NAME/industrial-design-intelligence-mvp.git
```

### 2. 在 Vercel 导入 GitHub 仓库

1. 打开 [Vercel](https://vercel.com/)。
2. 使用 GitHub 账号登录。
3. 点击 `Add New...`。
4. 选择 `Project`。
5. 在列表里找到 `industrial-design-intelligence-mvp`。
6. 点击 `Import`。

### 3. Vercel 构建配置

Framework Preset 选择：

```text
Vite
```

Build Command 填：

```bash
npm run build
```

Output Directory 填：

```text
dist
```

Install Command 一般保持默认：

```bash
npm install
```

### 4. 部署成功后获得公网链接

点击 `Deploy` 后，Vercel 会自动安装依赖并执行 `npm run build`。

部署成功后，Vercel 会给你一个公网地址，通常类似：

```text
https://industrial-design-intelligence-mvp.vercel.app
```

之后你可以在 Vercel 项目的 `Domains` 里查看、复制或绑定自定义域名。

### 5. 手机上访问

把 Vercel 生成的公网链接发到手机微信、浏览器或备忘录里，直接打开即可。这个项目是静态前端，日报 JSON 会从同一个站点的 `/data/latest.json` 和 `/data/reports/*.json` 读取。

### 6. 如果刷新页面 404 怎么解决

当前项目没有使用 React Router 的多页面路由，但已经提供了 `vercel.json`：

```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

这个配置会把非静态文件请求回退到 `index.html`，适合后续如果增加前端路由时避免刷新 404。

如果未来你添加了真实多页面路由，并且某个页面刷新后 404，优先检查：

1. `vercel.json` 是否已经提交到 GitHub。
2. Vercel 是否重新部署了最新 commit。
3. 数据文件是否仍在 `public/data/` 下，能通过 `/data/latest.json` 访问。

以后接入 GitHub Actions 后，让 Actions 在 build 前更新 `data/` 和 `public/data/` 即可。

## 部署到腾讯云 CloudBase

当前项目已部署到腾讯云 CloudBase 环境：

```text
Environment ID: industrial-design-intell-db80779
Service Name: industrial-design-intelligence-mvp
Public URL: https://industrial-design-int-6b7cf321-industrial-design-intell-db80779.webapps.tcloudbase.com/
```

CloudBase 配置写在 `cloudbaserc.json`。如果以后本地改完代码，要重新部署：

```bash
npm run build
tcb app deploy industrial-design-intelligence-mvp --env-id industrial-design-intell-db80779 --framework static --install-command "" --build-command "" --output-dir dist --deploy-path / --force
```

如果 `tcb` 不存在，先安装 CloudBase CLI：

```bash
npm install -g @cloudbase/cli
tcb login
```

当前使用的是 CloudBase 测试域名，第一次访问可能出现腾讯云“风险提醒”中间页，点击“确定访问”即可进入。若要去掉中间页，需要在 CloudBase 控制台绑定自定义域名或配置正式访问域名。
