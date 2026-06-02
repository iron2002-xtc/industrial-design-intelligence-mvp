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
  matchScore: number;
  reason: string;
  url: string;
  date: string;
  keywords: string[];
};

export type ReportAction = {
  id: string;
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
  keywords: string[];
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
  topNews: NewsItem[];
  trends: TrendItem[];
  aiTools: NewsItem[];
  hardwareObservation: NewsItem[];
  jobs: JobItem[];
  actions: ReportAction[];
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
