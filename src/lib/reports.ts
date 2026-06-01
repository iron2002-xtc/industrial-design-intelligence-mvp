import type { DailyReport, ReportIndexItem } from "../types/report";

const dataBase = `${import.meta.env.BASE_URL}data`;

async function readJson<T>(path: string): Promise<T> {
  const response = await fetch(`${dataBase}/${path}`, { cache: "no-cache" });

  if (!response.ok) {
    throw new Error(`数据读取失败：${path} (${response.status})`);
  }

  return (await response.json()) as T;
}

export function loadLatestReport() {
  return readJson<DailyReport>("latest.json");
}

export function loadReportsIndex() {
  return readJson<ReportIndexItem[]>("reportsIndex.json");
}

export function loadReportByDate(date: string) {
  return readJson<DailyReport>(`reports/${date}.json`);
}
