import {
  Activity,
  Bot,
  BriefcaseBusiness,
  CalendarDays,
  Clock3,
  Database,
  ExternalLink,
  FileStack,
  Lightbulb,
  Newspaper,
  Radar,
  Search,
  Sparkles,
  Target,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { HistoryRail } from "./components/HistoryRail";
import { InsightCard } from "./components/InsightCard";
import { JobsSection } from "./components/JobsSection";
import { MetricCard } from "./components/MetricCard";
import { SectionCard } from "./components/SectionCard";
import { TrendsSection } from "./components/TrendsSection";
import { getSearchResults } from "./lib/search";
import { loadLatestReport, loadReportByDate, loadReportsIndex } from "./lib/reports";
import type { DailyReport, ReportIndexItem } from "./types/report";

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
  const highMatchJobs = report?.jobs.filter((job) => job.matchScore >= 90) ?? [];
  const topJobs = useMemo(
    () => (report ? [...report.jobs].sort((a, b) => b.matchScore - a.matchScore).slice(0, 5) : []),
    [report],
  );
  const searchResults = useMemo(
    () => (report ? getSearchResults(report, searchQuery) : []),
    [report, searchQuery],
  );

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
                    工业设计情报站
                  </h1>
                  <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-600 sm:text-base">
                    面向 3C、智能硬件、清洁电器、机器人、AI硬件、家电、CMF 和作品集求职的个人情报中控台。
                  </p>
                  <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
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
                  </div>
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
                      搜索标题、摘要、公司、城市、方向、关键词
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

            <div className="grid gap-3 p-4 sm:grid-cols-2 sm:p-5 xl:grid-cols-4">
              <MetricCard
                label="今日新闻数"
                value={report.topNews.length}
                helper="优先展示与求职、趋势和作品集相关的信号"
                icon={<Newspaper size={20} />}
                tone="ink"
              />
              <MetricCard
                label="今日岗位数"
                value={report.jobs.length}
                helper="目标公司和重点城市的 mock 岗位池"
                icon={<BriefcaseBusiness size={20} />}
                tone="green"
              />
              <MetricCard
                label="高匹配岗位数"
                value={highMatchJobs.length}
                helper="匹配度 90+，建议优先准备投递材料"
                icon={<Target size={20} />}
                tone="copper"
              />
              <MetricCard
                label="趋势观察数"
                value={report.trends.length}
                helper="覆盖 AI硬件、3C、清洁电器、CMF 等方向"
                icon={<Activity size={20} />}
                tone="plum"
              />
            </div>
          </header>

          {isLoading && (
            <div className="rounded-lg border border-line bg-white/80 px-4 py-3 text-sm font-medium text-zinc-500 shadow-tight">
              正在切换日报数据...
            </div>
          )}

          {searchQuery.trim() && (
            <SectionCard
              eyebrow="Search"
              title={`搜索结果：${searchResults.length} 条`}
              description={`当前日报内匹配“${searchQuery}”的新闻、趋势、岗位和行动建议。`}
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

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]">
            <SectionCard
              eyebrow="Daily Briefing"
              title="今日重点新闻"
              description="先看最影响作品集、秋招和产品判断的 5 条信号。"
            >
              <div className="grid gap-3 lg:grid-cols-2">
                {report.topNews.map((item, index) => (
                  <InsightCard key={item.id} item={item} compact={index > 1} />
                ))}
              </div>
            </SectionCard>

            <div className="space-y-4">
              <SectionCard
                eyebrow="Design Trends"
                title="今日设计趋势 3 条"
                description="适合直接转化为作品集页面或小红书选题。"
              >
                <div className="space-y-3">
                  {report.trends.slice(0, 3).map((trend) => (
                    <article key={trend.id} className="rounded-lg border border-line bg-white p-4">
                      <span className="rounded-md bg-plum/10 px-2 py-1 text-xs font-semibold text-plum">
                        {trend.category}
                      </span>
                      <h3 className="mt-3 text-base font-semibold leading-snug text-ink">{trend.title}</h3>
                      <p className="mt-3 text-sm leading-6 text-zinc-600">{trend.trendSummary}</p>
                    </article>
                  ))}
                </div>
              </SectionCard>

              <SectionCard eyebrow="Next Actions" title="今天最值得做的 3 件事">
                <div className="space-y-3">
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
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            <SectionCard
              eyebrow="AI Design"
              title="AI设计与工具动态"
              description="把工具看作作品集和情报整理的辅助流程，而不是最终答案。"
              action={<Bot className="text-signal" size={24} />}
            >
              <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-1 2xl:grid-cols-3">
                {report.aiTools.map((item) => (
                  <InsightCard key={item.id} item={item} compact />
                ))}
              </div>
            </SectionCard>

            <SectionCard
              eyebrow="Hardware Watch"
              title="智能硬件 / 机器人 / 清洁电器观察"
              description="从产品系统、状态表达和维护路径里找作品集切入点。"
              action={<Radar className="text-copper" size={24} />}
            >
              <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-1 2xl:grid-cols-3">
                {report.hardwareObservation.map((item) => (
                  <InsightCard key={item.id} item={item} compact />
                ))}
              </div>
            </SectionCard>
          </div>

          <SectionCard
            eyebrow="Best Matched"
            title="今日优先关注岗位"
            description="首页先展示前 5 个高匹配机会，完整筛选在招聘区块里。"
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
          </SectionCard>

          <JobsSection jobs={report.jobs} searchQuery={searchQuery} />
          <TrendsSection trends={report.trends} />

          <footer className="rounded-lg border border-line bg-white/70 px-4 py-5 text-sm leading-6 text-zinc-500">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <span className="inline-flex items-center gap-2">
                <Lightbulb size={16} />
                当前为静态 JSON 数据结构版，后续可接入定时抓取、日报归档和真实原始链接。
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
