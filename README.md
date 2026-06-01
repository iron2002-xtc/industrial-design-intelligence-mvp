# 工业设计情报站 MVP

这是一个面向工业设计学生/设计师的本地 Dashboard 原型，聚合工业设计新闻、设计趋势、AI 工具动态、智能硬件/机器人/清洁电器观察、招聘机会和每日行动建议。

当前版本仍使用 mock 数据，但已经改造成适合后续自动更新和静态部署的数据结构：

- `data/`：项目根目录下的 canonical JSON 数据，适合 GitHub Actions 生成并提交。
- `public/data/`：前端静态读取的数据镜像，Vite/Vercel 会以 `/data/...` 路径提供。
- `scripts/`：生成 mock 数据和校验数据结构的 Python 脚本。

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
- 每个 report 是否包含 `topNews`、`trends`、`aiTools`、`hardwareObservation`、`jobs`、`actions`。
- `newsCount`、`jobsCount`、`trendsCount`、`highMatchJobsCount` 是否与日报内容一致。

## Build

```bash
npm run build
```

构建产物在 `dist/`。

## 数据结构

核心类型在 `src/types/report.ts`。

`DailyReport` 包含：

- `date`
- `title`
- `summary`
- `generatedAt`
- `sourceCount`
- `totalItems`
- `topNews`
- `trends`
- `aiTools`
- `hardwareObservation`
- `jobs`
- `actions`

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

1. 新增数据源配置，例如设计媒体 RSS、目标公司招聘页、公开岗位聚合页、手动维护的小红书选题源。
2. 抓取后做清洗、去重、分类、关键词提取和匹配度评分。
3. 生成同样结构的 `DailyReport` JSON。
4. 保留 `validate_data.py` 作为 CI 质量门槛。
5. 用 GitHub Actions 每天定时运行脚本，自动提交 `data/` 和 `public/data/`。

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
