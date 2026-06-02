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
};

export type JobItem = {
  id: string;
  company: string;
  title: string;
  city: string;
  direction: string;
  experience: string;
  jobType?: string;
  matchScore: number;
  sourceQualityScore?: number;
  relevanceScore?: number;
  reason: string;
  requirementsSummary?: string;
  url: string;
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
