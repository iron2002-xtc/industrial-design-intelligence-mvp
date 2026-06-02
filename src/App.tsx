import {
  Activity,
  BriefcaseBusiness,
  CalendarDays,
  Clock3,
  Database,
  ExternalLink,
  FileStack,
  Lightbulb,
  Radar,
  Search,
  Sparkles,
  Target,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { HistoryRail } from "./components/HistoryRail";
import { JobsSection } from "./components/JobsSection";
import { MetricCard } from "./components/MetricCard";
import { SectionCard } from "./components/SectionCard";
import {
  getJobActionLabel,
  getJobActionUrl,
  getQualityReport,
  isPriorityHighMatchJob,
  isTrustedHighMatchJob,
  normalizeJob,
  sourceTypeLabel,
} from "./lib/jobVerification";
import { getSearchResults } from "./lib/search";
import { loadLatestReport, loadReportByDate, loadReportsIndex } from "./lib/reports";
import type { CompanyUpdateItem, DailyReport, DesignHotspotItem, NewsItem, ReportIndexItem, TrendItem } from "./types/report";

const formatGeneratedAt = (value: string) => {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
    hour12: false,
  }).format(date);
};

const dataModeLabel: Record<NonNullable<DailyReport["dataMode"]>, string> = {
  Real: "Real",
  Fallback: "Fallback",
  Mock: "Mock",
};

const legacyNewsToHotspot = (item: NewsItem): DesignHotspotItem => ({
  id: item.id,
  title: item.title,
  summary: item.summary,
  source: item.source,
  category: item.category,
  url: item.url,
  date: item.date,
  importanceScore: item.importanceScore,
  sourceQualityScore: item.source === "Fallback Rule" ? 60 : 78,
  relevanceScore: item.importanceScore,
  designInsight: item.designInsight,
  relatedCompanies: [],
  tags: item.keywords ?? [],
});

const legacyTrendToHotspot = (item: TrendItem): DesignHotspotItem => ({
  id: item.id,
  title: item.title,
  summary: item.trendSummary,
  source: item.relatedCases[0] ?? "趋势观察",
  category: item.category,
  url: item.url,
  date: item.date,
  importanceScore: 82,
  sourceQualityScore: 70,
  relevanceScore: 82,
  designInsight: item.designInspiration,
  relatedCompanies: item.relatedCases,
  tags: item.keywords ?? [],
});

function App() {
  const [activeDate, setActiveDate] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [reportsIndex, setReportsIndex] = useState<ReportIndexItem[]>([]);
  const [reportsByDate, setReportsByDate] = useState<Record<string, DailyReport>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function bootstrap() {
      try {
        setIsLoading(true);
        const [latestReport, index] = await Promise.all([loadLatestReport(), loadReportsIndex()]);

        if (!mounted) return;

        setReportsIndex(index);
        setReportsByDate({ [latestReport.date]: latestReport });
        setActiveDate(latestReport.date);
        setError(null);
      } catch (err) {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : "数据初始化失败");
      } finally {
        if (mounted) setIsLoading(false);
      }
    }

    bootstrap();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!activeDate || reportsByDate[activeDate]) return;

    let mounted = true;

    async function fetchReport() {
      try {
        setIsLoading(true);
        const nextReport = await loadReportByDate(activeDate);

        if (!mounted) return;

        setReportsByDate((current) => ({
          ...current,
          [nextReport.date]: nextReport,
        }));
        setError(null);
      } catch (err) {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : `读取 ${activeDate} 日报失败`);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }

    fetchReport();

    return () => {
      mounted = false;
    };
  }, [activeDate, reportsByDate]);

  const report = activeDate ? reportsByDate[activeDate] : undefined;
  const jobOpportunities = useMemo(
    () => (report?.jobOpportunities ?? report?.jobs ?? []).map(normalizeJob),
    [report],
  );
  const highMatchJobs = (
    report?.highMatchJobs ? report.highMatchJobs.map(normalizeJob) : jobOpportunities.filter(isTrustedHighMatchJob)
  ).filter(isTrustedHighMatchJob);
  const designHotspots =
    report?.designHotspots ??
    [
      ...(report?.topNews ?? []).map(legacyNewsToHotspot),
      ...(report?.trends ?? []).map(legacyTrendToHotspot),
    ];
  const companyUpdates: CompanyUpdateItem[] = report?.companyUpdates ?? [];
  const qualityReport = report ? getQualityReport(report, jobOpportunities, designHotspots) : undefined;
  const highQualitySourceCount = new Set(
    [
      ...jobOpportunities.filter((item) => (item.confidenceScore ?? 0) >= 75).map((item) => item.company),
      ...designHotspots.filter((item) => (item.confidenceScore ?? item.sourceQualityScore) >= 75).map((item) => item.source),
      ...companyUpdates.filter((item) => item.relevanceScore >= 80).map((item) => item.company),
    ],
  ).size;
  const topJobs = useMemo(
    () => [...highMatchJobs].sort((a, b) => b.matchScore - a.matchScore).slice(0, 5),
    [highMatchJobs],
  );
  const priorityHighMatchJobs = useMemo(
    () => [...jobOpportunities].filter(isPriorityHighMatchJob).sort((a, b) => b.matchScore - a.matchScore),
    [jobOpportunities],
  );
  const unverifiedHighRelevantJobs = useMemo(
    () =>
      [...jobOpportunities]
        .filter((job) => job.verificationStatus === "unverified")
        .filter((job) => job.matchScore >= 75 || (job.relevanceScore ?? 0) >= 80)
        .sort((a, b) => b.matchScore - a.matchScore),
    [jobOpportunities],
  );
  const alertJobs = useMemo(() => {
    if (priorityHighMatchJobs.length > 0) return priorityHighMatchJobs.slice(0, 3);
    if (unverifiedHighRelevantJobs.length > 0) return unverifiedHighRelevantJobs.slice(0, 3);
    return [...jobOpportunities].sort((a, b) => b.matchScore - a.matchScore).slice(0, 3);
  }, [jobOpportunities, priorityHighMatchJobs, unverifiedHighRelevantJobs]);
  const jobAlertMessage =
    priorityHighMatchJobs.length > 0
      ? `今天有 ${priorityHighMatchJobs.length} 个高可信高匹配岗位，建议优先查看。`
      : unverifiedHighRelevantJobs.length > 0
        ? `今天暂无高可信高匹配岗位，有 ${unverifiedHighRelevantJobs.length} 个待核实岗位可作为线索。`
        : "今天暂无特别值得优先关注的岗位，建议只浏览设计热点。";
  const alertTone =
    priorityHighMatchJobs.length > 0
      ? "border-signal/30 bg-signal/5"
      : unverifiedHighRelevantJobs.length > 0
        ? "border-copper/30 bg-copper/10"
        : "border-line bg-white";
  const searchResults = useMemo(
    () => (report ? getSearchResults({ ...report, jobOpportunities, jobs: jobOpportunities }, searchQuery) : []),
    [jobOpportunities, report, searchQuery],
  );
  const dataMode = report?.dataMode ?? "Mock";
  const shouldShowStatusWarning =
    report?.collectionStatus === "partial" || report?.collectionStatus === "fallback";

  const handleDateChange = (date: string) => {
    setActiveDate(date);
  };

  if (error && !report) {
    return (
      <main className="min-h-screen px-3 py-4 text-ink sm:px-5 lg:px-6">
        <div className="mx-auto max-w-3xl rounded-lg border border-line bg-white p-6 shadow-soft">
          <p className="label">Data Error</p>
          <h1 className="mt-3 text-2xl font-semibold">数据读取失败</h1>
          <p className="mt-3 text-sm leading-6 text-zinc-600">{error}</p>
          <p className="mt-4 text-sm leading-6 text-zinc-500">
            请先运行 npm run generate:mock 和 npm run validate:data。
          </p>
        </div>
      </main>
    );
  }

  if (!report) {
    return (
      <main className="flex min-h-screen items-center justify-center px-4 text-ink">
        <div className="rounded-lg border border-line bg-white p-6 text-center shadow-soft">
          <p className="label">Loading</p>
          <h1 className="mt-3 text-2xl font-semibold">正在读取工业设计日报</h1>
          <p className="mt-3 text-sm text-zinc-500">
            从 /data/latest.json 和 /data/reportsIndex.json 加载中。
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-3 py-4 text-ink sm:px-5 lg:px-6">
      <div className="mx-auto grid max-w-[1500px] gap-4 lg:grid-cols-[290px_minmax(0,1fr)]">
        <HistoryRail reports={reportsIndex} activeDate={activeDate} onChange={handleDateChange} />

        <div className="space-y-4">
          <header className="card overflow-hidden">
            <div className="border-b border-line bg-white px-4 py-4 sm:px-6">
              <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-md bg-ink px-2.5 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-white">
                      ID Intel
                    </span>
                    <span className="rounded-md bg-signal/10 px-2.5 py-1.5 text-xs font-semibold text-signal">
                      {report.date}
                    </span>
                  </div>
                  <h1 className="mt-4 text-3xl font-semibold tracking-normal text-ink sm:text-4xl">
                    工业设计求职与设计热点日报
                  </h1>
                  <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-600 sm:text-base">
                    聚焦工业设计求职机会、目标公司动态、产品设计热点、CMF、3C、智能硬件、机器人与家电趋势。
                  </p>
                  <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
                    <span className="inline-flex items-center gap-2 rounded-md border border-line bg-zinc-50 px-3 py-2 text-xs font-medium text-zinc-600">
                      <CalendarDays size={14} />
                      日报日期 {report.date}
                    </span>
                    <span className="inline-flex items-center gap-2 rounded-md border border-line bg-zinc-50 px-3 py-2 text-xs font-medium text-zinc-600">
                      <Clock3 size={14} />
                      生成 {formatGeneratedAt(report.generatedAt)}
                    </span>
                    <span className="inline-flex items-center gap-2 rounded-md border border-line bg-zinc-50 px-3 py-2 text-xs font-medium text-zinc-600">
                      <Database size={14} />
                      来源 {report.sourceCount} 个
                    </span>
                    <span className="inline-flex items-center gap-2 rounded-md border border-line bg-zinc-50 px-3 py-2 text-xs font-medium text-zinc-600">
                      <FileStack size={14} />
                      收录 {report.totalItems} 条
                    </span>
                    <span className="inline-flex items-center gap-2 rounded-md border border-line bg-zinc-50 px-3 py-2 text-xs font-medium text-zinc-600">
                      <Sparkles size={14} />
                      模式 {dataModeLabel[dataMode]}
                    </span>
                  </div>
                  {shouldShowStatusWarning && (
                    <div className="mt-3 rounded-md border border-copper/30 bg-copper/10 px-3 py-2 text-sm leading-6 text-copper">
                      {report.statusMessage || "今日部分数据抓取失败，已使用备用数据。"}
                    </div>
                  )}
                  {qualityReport && (
                    <p className="mt-3 text-sm leading-6 text-zinc-500">
                      今日收集 {qualityReport.totalCollected} 条，过滤{" "}
                      {Math.max(0, qualityReport.totalCollected - qualityReport.afterQualityFilter)} 条，
                      高可信岗位 {qualityReport.verifiedJobsCount + qualityReport.likelyJobsCount} 个，
                      待核实岗位 {qualityReport.unverifiedJobsCount} 个。
                    </p>
                  )}
                </div>

                <div className="grid gap-3 sm:grid-cols-[180px_minmax(260px,420px)]">
                  <label className="block">
                    <span className="mb-2 flex items-center gap-2 text-xs font-semibold text-zinc-500">
                      <CalendarDays size={14} />
                      日期切换
                    </span>
                    <select
                      value={activeDate}
                      onChange={(event) => setActiveDate(event.target.value)}
                      className="focus-ring w-full rounded-md border border-line bg-white px-3 py-3 text-sm font-medium text-zinc-700"
                    >
                      {reportsIndex.map((item) => (
                        <option key={item.date} value={item.date}>
                          {item.date}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="block">
                    <span className="mb-2 flex items-center gap-2 text-xs font-semibold text-zinc-500">
                      <Search size={14} />
                      搜索岗位、设计热点、公司、城市、方向、关键词
                    </span>
                    <div className="relative">
                      <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" size={18} />
                      <input
                        value={searchQuery}
                        onChange={(event) => setSearchQuery(event.target.value)}
                        placeholder="例如：大疆 / 深圳 / CMF / 清洁电器"
                        className="focus-ring w-full rounded-md border border-line bg-white py-3 pl-10 pr-3 text-sm text-zinc-700 placeholder:text-zinc-400"
                      />
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <div className="grid gap-3 p-4 sm:grid-cols-2 sm:p-5 xl:grid-cols-5">
              <MetricCard
                label="今日岗位数"
                value={jobOpportunities.length}
                helper="覆盖官网招聘、公开招聘入口和高质量搜索线索"
                icon={<BriefcaseBusiness size={20} />}
                tone="ink"
              />
              <MetricCard
                label="高匹配岗位数"
                value={highMatchJobs.length}
                helper="必须满足 match 85+、confidence 75+、verified/likely"
                icon={<Target size={20} />}
                tone="green"
              />
              <MetricCard
                label="今日设计热点数"
                value={designHotspots.length}
                helper="低相关度内容已过滤，保留产品设计强相关信号"
                icon={<Activity size={20} />}
                tone="copper"
              />
              <MetricCard
                label="高可信来源数"
                value={highQualitySourceCount}
                helper={report.qualitySummary ?? "过滤低质量搜索结果后保留"}
                icon={<Database size={20} />}
                tone="plum"
              />
              <MetricCard
                label="最近更新时间"
                value={formatGeneratedAt(report.generatedAt)}
                helper={report.qualitySummary ?? "每日北京时间 7:30 自动更新"}
                icon={<Clock3 size={20} />}
                tone="ink"
              />
            </div>
          </header>

          {isLoading && (
            <div className="rounded-lg border border-line bg-white/80 px-4 py-3 text-sm font-medium text-zinc-500 shadow-tight">
              正在切换日报数据...
            </div>
          )}

          <section className={`rounded-lg border p-4 shadow-tight sm:p-5 ${alertTone}`}>
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <p className="label">Job Alert</p>
                <h2 className="mt-2 text-xl font-semibold text-ink">今日重点岗位提醒</h2>
                <p className="mt-2 text-sm leading-6 text-zinc-600">{jobAlertMessage}</p>
              </div>
              <span className="inline-flex w-fit items-center gap-2 rounded-md bg-white px-3 py-2 text-xs font-semibold text-zinc-600 shadow-tight">
                <Target size={15} />
                高可信 {qualityReport?.verifiedJobsCount ?? 0} / 较可信 {qualityReport?.likelyJobsCount ?? 0}
              </span>
            </div>

            {alertJobs.length > 0 && (
              <div className="mt-4 grid gap-3 lg:grid-cols-3">
                {alertJobs.map((job) => (
                  <article key={job.id} className="rounded-lg border border-line bg-white p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-zinc-500">{job.company}</p>
                        <h3 className="mt-1 text-base font-semibold leading-snug text-ink">{job.title}</h3>
                      </div>
                      <span className="shrink-0 rounded-md bg-ink px-2 py-1 text-sm font-semibold text-white">
                        {job.matchScore}
                      </span>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs font-medium">
                      <span className="rounded-md bg-zinc-100 px-2 py-1 text-zinc-600">{job.city}</span>
                      <span className="rounded-md bg-zinc-100 px-2 py-1 text-zinc-600">可信度 {job.confidenceScore}</span>
                      <span className="rounded-md bg-zinc-100 px-2 py-1 text-zinc-600">
                        {sourceTypeLabel[job.sourceType]}
                      </span>
                    </div>
                    <a
                      href={getJobActionUrl(job)}
                      target="_blank"
                      rel="noreferrer"
                      className="focus-ring mt-4 inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium text-zinc-700 transition hover:border-zinc-300 hover:bg-zinc-50"
                    >
                      {getJobActionLabel(job)}
                      <ExternalLink size={15} />
                    </a>
                  </article>
                ))}
              </div>
            )}
          </section>

          {searchQuery.trim() && (
            <SectionCard
              eyebrow="Search"
              title={`搜索结果：${searchResults.length} 条`}
              description={`当前日报内匹配“${searchQuery}”的岗位、设计热点、公司动态和行动建议。`}
            >
              <div className="grid gap-3 lg:grid-cols-2">
                {searchResults.map((result) => (
                  <article key={result.id} className="rounded-lg border border-line bg-white p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <span className="rounded-md bg-zinc-100 px-2 py-1 text-xs font-semibold text-zinc-600">
                          {result.type}
                        </span>
                        <h3 className="mt-3 text-base font-semibold leading-snug text-ink">{result.title}</h3>
                      </div>
                      {typeof result.score === "number" && (
                        <span className="rounded-md bg-signal/10 px-2 py-1 text-xs font-semibold text-signal">
                          {result.score}
                        </span>
                      )}
                    </div>
                    <p className="mt-3 text-sm leading-6 text-zinc-600">{result.summary}</p>
                    <p className="mt-3 text-xs font-medium text-zinc-400">{result.meta}</p>
                    {result.url && (
                      <a
                        href={result.url}
                        target="_blank"
                        rel="noreferrer"
                        className="focus-ring mt-4 inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium text-zinc-700 transition hover:border-zinc-300 hover:bg-zinc-50"
                      >
                        原始链接
                        <ExternalLink size={15} />
                      </a>
                    )}
                  </article>
                ))}
              </div>
              {searchResults.length === 0 && (
                <div className="rounded-lg border border-dashed border-line bg-zinc-50 px-4 py-8 text-center text-sm text-zinc-500">
                  暂时没有结果，可以换一个公司、城市、方向或关键词。
                </div>
              )}
            </SectionCard>
          )}

          <SectionCard
            eyebrow="Best Matched"
            title="高匹配岗位"
            description="按目标公司、城市优先级、方向相关度、经验匹配和来源质量综合排序。"
            action={<Sparkles className="text-signal" size={24} />}
          >
            <div className="grid gap-3 lg:grid-cols-5">
              {topJobs.map((job) => (
                <a
                  key={job.id}
                  href={job.url}
                  target="_blank"
                  rel="noreferrer"
                  className="focus-ring rounded-lg border border-line bg-white p-4 transition hover:-translate-y-0.5 hover:shadow-tight"
                >
                  <span className="rounded-md bg-zinc-100 px-2 py-1 text-xs font-semibold text-zinc-600">
                    {job.city} / {job.direction}
                  </span>
                  <h3 className="mt-3 text-base font-semibold leading-snug text-ink">{job.company}</h3>
                  <p className="mt-1 text-sm text-zinc-600">{job.title}</p>
                  <div className="mt-4 flex items-center justify-between">
                    <span className="text-2xl font-semibold text-signal">{job.matchScore}</span>
                    <ExternalLink size={15} className="text-zinc-400" />
                  </div>
                </a>
              ))}
            </div>
            {topJobs.length === 0 && (
              <div className="rounded-lg border border-dashed border-line bg-zinc-50 px-4 py-8 text-center text-sm text-zinc-500">
                今天没有通过真实性校验的高匹配岗位。可以先查看下方“待核实岗位”，但不要直接按高匹配优先级投递。
              </div>
            )}
          </SectionCard>

          <JobsSection jobs={jobOpportunities} searchQuery={searchQuery} />

          <SectionCard
            eyebrow="Design Hotspots"
            title="设计热点"
            description="只保留与产品设计强相关的趋势、案例、CMF、3C、AI硬件、机器人、家电和设计奖项信息。"
            action={<Radar className="text-copper" size={24} />}
          >
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {designHotspots.map((item) => (
                <article key={item.id} className="rounded-lg border border-line bg-white p-4 transition hover:-translate-y-0.5 hover:shadow-tight">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="rounded-md bg-zinc-100 px-2 py-1 text-xs font-semibold text-zinc-600">
                        {item.category}
                      </span>
                      <h3 className="mt-3 text-base font-semibold leading-snug text-ink">{item.title}</h3>
                    </div>
                    <span className="shrink-0 rounded-md bg-signal/10 px-2 py-1 text-xs font-semibold text-signal">
                      {item.relevanceScore}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-zinc-600">{item.summary}</p>
                  <div className="mt-3 grid gap-2 text-xs font-medium text-zinc-500 sm:grid-cols-2">
                    <span className="rounded-md bg-zinc-50 px-2 py-1">产品类别：{item.productCategory ?? item.category}</span>
                    <span className="rounded-md bg-zinc-50 px-2 py-1">相关品牌：{item.relatedBrand || item.relatedCompanies.join("、") || item.source}</span>
                    <span className="rounded-md bg-zinc-50 px-2 py-1">来源可信度：{item.confidenceScore ?? item.sourceQualityScore}</span>
                    <span className="rounded-md bg-zinc-50 px-2 py-1">相关度：{item.relevanceScore}</span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-zinc-500">
                    设计相关性：{item.designRelevanceReason ?? item.designInsight}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-zinc-500">设计启发：{item.designInsight}</p>
                  {item.evidenceText && (
                    <p className="mt-2 text-xs leading-5 text-zinc-400">证据片段：{item.evidenceText}</p>
                  )}
                  <div className="mt-3 flex flex-wrap gap-2">
                    {item.tags.slice(0, 5).map((tag) => (
                      <span key={tag} className="rounded-md bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-500">
                        {tag}
                      </span>
                    ))}
                    {item.sourceQualityScore >= 85 && (
                      <span className="rounded-md bg-ink px-2 py-1 text-xs font-medium text-white">高可信</span>
                    )}
                  </div>
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="focus-ring mt-4 inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium text-zinc-700 transition hover:border-zinc-300 hover:bg-zinc-50"
                  >
                    原始链接
                    <ExternalLink size={15} />
                  </a>
                </article>
              ))}
            </div>
          </SectionCard>

          <SectionCard
            eyebrow="Company Updates"
            title="公司动态"
            description="只保留目标公司中与产品设计、招聘、校招、新品发布、设计团队相关的动态。"
          >
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {companyUpdates.map((item) => (
                <article key={item.id} className="rounded-lg border border-line bg-white p-4">
                  <span className="rounded-md bg-signal/10 px-2 py-1 text-xs font-semibold text-signal">
                    {item.company}
                  </span>
                  <h3 className="mt-3 text-base font-semibold leading-snug text-ink">{item.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-zinc-600">{item.summary}</p>
                  <p className="mt-3 text-sm leading-6 text-zinc-500">设计关联：{item.designRelation}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {item.tags.slice(0, 4).map((tag) => (
                      <span key={tag} className="rounded-md bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-500">
                        {tag}
                      </span>
                    ))}
                  </div>
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="focus-ring mt-4 inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium text-zinc-700 transition hover:border-zinc-300 hover:bg-zinc-50"
                  >
                    原始链接
                    <ExternalLink size={15} />
                  </a>
                </article>
              ))}
            </div>
          </SectionCard>

          <SectionCard eyebrow="Next Actions" title="今日求职与作品集行动">
            <div className="grid gap-3 md:grid-cols-3">
              {report.actions.map((action, index) => (
                <div key={action.id} className="flex gap-3 rounded-lg border border-line bg-white p-4">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-ink text-sm font-semibold text-white">
                    {index + 1}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-ink">{action.title}</p>
                    <p className="mt-1 text-sm leading-6 text-zinc-700">{action.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>

          {qualityReport && qualityReport.companyCrawlStatus.length > 0 && (
            <SectionCard
              eyebrow="Source Status"
              title="公司官网抓取状态"
              description={`已配置 ${qualityReport.configuredOfficialCompanies} 家官网源，成功 ${qualityReport.successfulOfficialCompanies} 家，无匹配 ${qualityReport.noMatchingOfficialCompanies} 家，失败 ${qualityReport.failedOfficialCompanies} 家。`}
            >
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                {qualityReport.companyCrawlStatus.map((item) => (
                  <div key={`${item.company}-${item.sourceUrl}`} className="rounded-md border border-line bg-white px-3 py-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate text-sm font-semibold text-ink">{item.company}</span>
                      <span
                        className={`rounded-md px-2 py-1 text-[11px] font-semibold ${
                          item.status === "success"
                            ? "bg-signal/10 text-signal"
                            : item.status === "no_matching_jobs"
                              ? "bg-zinc-100 text-zinc-600"
                              : "bg-copper/10 text-copper"
                        }`}
                      >
                        {item.status}
                      </span>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-zinc-500">
                      匹配 {item.matchedCount} 条
                      {item.message ? ` / ${item.message}` : ""}
                    </p>
                  </div>
                ))}
              </div>
            </SectionCard>
          )}

          <footer className="rounded-lg border border-line bg-white/70 px-4 py-5 text-sm leading-6 text-zinc-500">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <span className="inline-flex items-center gap-2">
                <Lightbulb size={16} />
                当前日报聚焦工业设计求职机会与产品设计热点，每天北京时间 7:30 自动更新。
              </span>
              <span>{report.title}</span>
            </div>
          </footer>
        </div>
      </div>
    </main>
  );
}

export default App;
