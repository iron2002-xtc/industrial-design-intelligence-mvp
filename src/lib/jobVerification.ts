import type { DailyReport, DesignHotspotItem, JobItem, QualityReport, SourceType, VerificationStatus } from "../types/report";

const verificationStatuses = new Set(["verified", "likely", "unverified", "fallback"]);
const sourceTypes = new Set(["official", "job_board", "search_result", "media", "fallback"]);

const defaultConfidence: Record<VerificationStatus, number> = {
  verified: 92,
  likely: 82,
  unverified: 55,
  fallback: 45,
};

export type NormalizedJobItem = JobItem & {
  verificationStatus: VerificationStatus;
  sourceType: SourceType;
  applyUrl: string;
  originalUrl: string;
  evidenceText: string;
  lastCheckedAt: string;
  confidenceScore: number;
};

export const verificationLabel: Record<VerificationStatus, string[]> = {
  verified: ["官网可验证", "高可信"],
  likely: ["招聘平台", "较可信"],
  unverified: ["待核实", "搜索线索"],
  fallback: ["备用数据"],
};

export const sourceTypeLabel: Record<SourceType, string> = {
  official: "官网来源",
  job_board: "招聘平台",
  search_result: "搜索来源",
  media: "媒体来源",
  fallback: "备用数据",
};

const asVerificationStatus = (value: string | undefined): VerificationStatus =>
  verificationStatuses.has(value ?? "") ? (value as VerificationStatus) : "unverified";

const asSourceType = (value: string | undefined, status: VerificationStatus): SourceType => {
  if (sourceTypes.has(value ?? "")) return value as SourceType;
  return status === "fallback" ? "fallback" : "search_result";
};

export function normalizeJob(job: JobItem): NormalizedJobItem {
  const verificationStatus = asVerificationStatus(job.verificationStatus);
  const sourceType = asSourceType(job.sourceType, verificationStatus);
  const rawConfidence = typeof job.confidenceScore === "number" ? job.confidenceScore : defaultConfidence[verificationStatus];
  const rawMatch = typeof job.matchScore === "number" ? job.matchScore : 0;
  const originalUrl = job.originalUrl || job.url || job.applyUrl || "#";
  const applyUrl =
    job.applyUrl || (verificationStatus === "verified" || verificationStatus === "likely" ? job.url || originalUrl : "");

  let confidenceScore = rawConfidence;
  let matchScore = rawMatch;

  if (verificationStatus === "fallback") {
    confidenceScore = Math.min(confidenceScore, 50);
    matchScore = Math.min(matchScore, 65);
  }

  if (verificationStatus === "unverified") {
    confidenceScore = Math.min(confidenceScore, 70);
    matchScore = Math.min(matchScore, 80);
  }

  if (sourceType === "search_result") {
    matchScore = Math.min(matchScore, 80);
  }

  return {
    ...job,
    verificationStatus,
    sourceType,
    applyUrl,
    originalUrl,
    url: job.url || originalUrl,
    evidenceText: job.evidenceText || "历史日报缺少校验证据，请打开原始链接核对。",
    lastCheckedAt: job.lastCheckedAt || job.date,
    confidenceScore,
    matchScore,
  } satisfies NormalizedJobItem;
}

export function isTrustedHighMatchJob(job: JobItem) {
  return (
    job.matchScore >= 85 &&
    (job.confidenceScore ?? 0) >= 75 &&
    (job.verificationStatus === "verified" || job.verificationStatus === "likely")
  );
}

export function isPriorityHighMatchJob(job: JobItem) {
  return isTrustedHighMatchJob(job) && job.matchScore >= 90;
}

export function getJobActionLabel(job: JobItem) {
  if (job.verificationStatus === "verified" && job.sourceType === "official") return "前往投递";
  if (job.verificationStatus === "likely") return "查看岗位";
  return "查看来源";
}

export function getJobActionUrl(job: JobItem) {
  if (job.verificationStatus === "verified" && job.sourceType === "official") {
    return job.applyUrl || job.originalUrl || job.url;
  }
  if (job.verificationStatus === "likely") {
    return job.applyUrl || job.originalUrl || job.url;
  }
  return job.originalUrl || job.url || job.applyUrl;
}

export function getQualityReport(
  report: DailyReport,
  jobs: JobItem[],
  hotspots: DesignHotspotItem[],
): QualityReport {
  const current = report.qualityReport;
  const verifiedJobsCount = jobs.filter((job) => job.verificationStatus === "verified").length;
  const likelyJobsCount = jobs.filter((job) => job.verificationStatus === "likely").length;
  const unverifiedJobsCount = jobs.filter((job) => job.verificationStatus === "unverified").length;
  const fallbackJobsCount = jobs.filter((job) => job.verificationStatus === "fallback").length;
  const officialSourceJobsCount = jobs.filter((job) => job.sourceType === "official").length;
  const jobBoardJobsCount = jobs.filter((job) => job.sourceType === "job_board").length;
  const searchResultJobsCount = jobs.filter((job) => job.sourceType === "search_result").length;
  const highMatchVerifiedJobsCount = jobs.filter(isTrustedHighMatchJob).length;

  return {
    totalCollected: current?.totalCollected ?? jobs.length + hotspots.length,
    afterDedup: current?.afterDedup ?? jobs.length + hotspots.length,
    afterQualityFilter: current?.afterQualityFilter ?? jobs.length + hotspots.length,
    verifiedJobsCount: current?.verifiedJobsCount ?? verifiedJobsCount,
    likelyJobsCount: current?.likelyJobsCount ?? likelyJobsCount,
    unverifiedJobsCount: current?.unverifiedJobsCount ?? unverifiedJobsCount,
    fallbackJobsCount: current?.fallbackJobsCount ?? fallbackJobsCount,
    officialSourceJobsCount: current?.officialSourceJobsCount ?? officialSourceJobsCount,
    jobBoardJobsCount: current?.jobBoardJobsCount ?? jobBoardJobsCount,
    searchResultJobsCount: current?.searchResultJobsCount ?? searchResultJobsCount,
    highMatchVerifiedJobsCount: current?.highMatchVerifiedJobsCount ?? highMatchVerifiedJobsCount,
    genericSearchResultsFiltered: current?.genericSearchResultsFiltered ?? 0,
    failedSources: current?.failedSources ?? [],
    companyCrawlStatus: current?.companyCrawlStatus ?? [],
  };
}
