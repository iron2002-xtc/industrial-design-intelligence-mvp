import type { CompanyUpdateItem, DailyReport, DesignHotspotItem, JobItem, NewsItem, TrendItem } from "../types/report";

export type SearchResult = {
  id: string;
  type: "设计热点" | "公司动态" | "新闻" | "趋势" | "AI工具" | "硬件观察" | "岗位" | "行动";
  title: string;
  summary: string;
  meta: string;
  url?: string;
  date: string;
  score?: number;
  searchableText: string;
};

const normalize = (value: string) => value.trim().toLowerCase();

const includesQuery = (result: SearchResult, query: string) =>
  normalize(result.searchableText).includes(normalize(query));

const newsToResult = (item: NewsItem, type: SearchResult["type"]): SearchResult => ({
  id: item.id,
  type,
  title: item.title,
  summary: item.summary,
  meta: `${item.source} / ${item.category}`,
  url: item.url,
  date: item.date,
  score: item.importanceScore,
  searchableText: [
    item.title,
    item.summary,
    item.source,
    item.category,
    item.designInsight,
    item.date,
    ...(item.keywords ?? []),
  ].join(" "),
});

const trendToResult = (item: TrendItem): SearchResult => ({
  id: item.id,
  type: "趋势",
  title: item.title,
  summary: item.trendSummary,
  meta: `${item.category} / ${item.relatedCases.join("、")}`,
  url: item.url,
  date: item.date,
  searchableText: [
    item.title,
    item.trendSummary,
    item.category,
    item.designInspiration,
    item.relatedCases.join(" "),
    ...(item.keywords ?? []),
  ].join(" "),
});

const jobToResult = (item: JobItem): SearchResult => ({
  id: item.id,
  type: "岗位",
  title: `${item.company} · ${item.title}`,
  summary: item.reason,
  meta: `${item.city} / ${item.direction} / ${item.experience}`,
  url: item.url,
  date: item.date,
  score: item.matchScore,
  searchableText: [
    item.company,
    item.title,
    item.city,
    item.direction,
    item.experience,
    item.reason,
    item.date,
    ...(item.keywords ?? []),
  ].join(" "),
});

const hotspotToResult = (item: DesignHotspotItem): SearchResult => ({
  id: item.id,
  type: "设计热点",
  title: item.title,
  summary: item.summary,
  meta: `${item.source} / ${item.category}`,
  url: item.url,
  date: item.date,
  score: item.relevanceScore,
  searchableText: [
    item.title,
    item.summary,
    item.source,
    item.category,
    item.designInsight,
    item.relatedCompanies.join(" "),
    item.tags.join(" "),
    item.date,
  ].join(" "),
});

const companyUpdateToResult = (item: CompanyUpdateItem): SearchResult => ({
  id: item.id,
  type: "公司动态",
  title: `${item.company} · ${item.title}`,
  summary: item.summary,
  meta: `${item.category} / ${item.designRelation}`,
  url: item.url,
  date: item.date,
  score: item.relevanceScore,
  searchableText: [
    item.company,
    item.title,
    item.summary,
    item.category,
    item.designRelation,
    item.tags.join(" "),
    item.date,
  ].join(" "),
});

export function getSearchResults(report: DailyReport, query: string): SearchResult[] {
  if (!query.trim()) return [];

  const jobs = report.jobOpportunities ?? report.jobs ?? [];
  const topNews = report.topNews ?? [];
  const aiTools = report.aiTools ?? [];
  const hardwareObservation = report.hardwareObservation ?? [];
  const trends = report.trends ?? [];

  const results: SearchResult[] = [
    ...(report.designHotspots ?? []).map(hotspotToResult),
    ...(report.companyUpdates ?? []).map(companyUpdateToResult),
    ...topNews.map((item) => newsToResult(item, "新闻")),
    ...aiTools.map((item) => newsToResult(item, "AI工具")),
    ...hardwareObservation.map((item) => newsToResult(item, "硬件观察")),
    ...trends.map(trendToResult),
    ...jobs.map(jobToResult),
    ...report.actions.map((action, index) => ({
      id: action.id || `${report.date}-action-${index + 1}`,
      type: "行动" as const,
      title: action.title || `今日行动 ${index + 1}`,
      summary: action.description,
      meta: "行动建议",
      date: report.date,
      searchableText: [
        action.title,
        action.description,
        action.priority,
        action.keywords.join(" "),
        report.date,
        "行动",
        "作品集",
        "秋招",
      ].join(" "),
    })),
  ];

  return results.filter((result) => includesQuery(result, query));
}

export function textMatches(fields: string[], query: string) {
  if (!query.trim()) return true;
  return normalize(fields.join(" ")).includes(normalize(query));
}
