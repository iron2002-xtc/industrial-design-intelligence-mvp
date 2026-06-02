export type NewsItem = {
  id: string;
  title: string;
  summary: string;
  source: string;
  category: string;
  url: string;
  date: string;
  importanceScore: number;
  designInsight: string;
  keywords: string[];
};

export type TrendItem = {
  id: string;
  title: string;
  trendSummary: string;
  relatedCases: string[];
  designInspiration: string;
  category: string;
  url: string;
  date: string;
  keywords: string[];
  designRelevanceReason?: string;
  productCategory?: string;
  relatedBrand?: string;
  isGenericSearchResult?: boolean;
  evidenceText?: string;
  confidenceScore?: number;
};

export type VerificationStatus = "verified" | "likely" | "unverified" | "fallback";
export type SourceType = "official" | "job_board" | "search_result" | "media" | "fallback";

export type JobItem = {
  id: string;
  company: string;
  title: string;
  city: string;
  direction: string;
  experience: string;
  jobType?: string;
  jobCategory?: string;
  matchScore: number;
  sourceQualityScore?: number;
  relevanceScore?: number;
  reason: string;
  responsibilitiesSummary?: string;
  requirementsSummary?: string;
  url: string;
  verificationStatus?: VerificationStatus;
  sourceType?: SourceType;
  applyUrl?: string;
  originalUrl?: string;
  evidenceText?: string;
  lastCheckedAt?: string;
  confidenceScore?: number;
  date: string;
  keywords?: string[];
  tags?: string[];
};

export type ReportAction = {
  id: string;
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
  keywords: string[];
};

export type DesignHotspotItem = {
  id: string;
  title: string;
  summary: string;
  source: string;
  category: string;
  url: string;
  date: string;
  importanceScore: number;
  sourceQualityScore: number;
  relevanceScore: number;
  designInsight: string;
  relatedCompanies: string[];
  tags: string[];
  designRelevanceReason?: string;
  productCategory?: string;
  relatedBrand?: string;
  isGenericSearchResult?: boolean;
  evidenceText?: string;
  confidenceScore?: number;
};

export type CompanyCrawlStatus = {
  company: string;
  status: "success" | "no_matching_jobs" | "blocked_or_failed" | "not_configured";
  sourceUrl: string;
  checkedAt: string;
  matchedCount: number;
  evidenceText?: string;
  message?: string;
};

export type QualityReport = {
  totalCollected: number;
  afterDedup: number;
  afterQualityFilter: number;
  verifiedJobsCount: number;
  likelyJobsCount: number;
  unverifiedJobsCount: number;
  fallbackJobsCount: number;
  officialSourceJobsCount: number;
  jobBoardJobsCount: number;
  searchResultJobsCount: number;
  highMatchVerifiedJobsCount: number;
  genericSearchResultsFiltered: number;
  configuredOfficialCompanies: number;
  successfulOfficialCompanies: number;
  noMatchingOfficialCompanies: number;
  failedOfficialCompanies: number;
  officialJobsFound: number;
  likelyJobsFound: number;
  unverifiedSearchLeads: number;
  highMatchJobsCount: number;
  verifiedJobDetailsChecked: number;
  verifiedJobsDowngraded: number;
  genericHotspotsFiltered: number;
  concreteHotspotsKept: number;
  jobDetailPagesFailed: number;
  jobDetailPagesPassed: number;
  failedSources: string[];
  companyCrawlStatus: CompanyCrawlStatus[];
};

export type CompanyUpdateItem = {
  id: string;
  company: string;
  title: string;
  summary: string;
  category: string;
  url: string;
  date: string;
  relevanceScore: number;
  designRelation: string;
  tags: string[];
};

export type DailyReport = {
  date: string;
  title: string;
  summary: string;
  generatedAt: string;
  sourceCount: number;
  totalItems: number;
  dataMode?: "Real" | "Fallback" | "Mock";
  collectionStatus?: "success" | "partial" | "fallback";
  statusMessage?: string;
  qualitySummary?: string;
  qualityReport?: QualityReport;
  jobOpportunities?: JobItem[];
  highMatchJobs?: JobItem[];
  designHotspots?: DesignHotspotItem[];
  companyUpdates?: CompanyUpdateItem[];
  actions: ReportAction[];
  topNews?: NewsItem[];
  trends?: TrendItem[];
  aiTools?: NewsItem[];
  hardwareObservation?: NewsItem[];
  jobs?: JobItem[];
};

export type ReportIndexItem = {
  date: string;
  title: string;
  summary: string;
  newsCount: number;
  jobsCount: number;
  trendsCount: number;
  highMatchJobsCount: number;
};
