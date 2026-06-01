import { CalendarDays, ChevronRight, History } from "lucide-react";
import type { ReportIndexItem } from "../types/report";

type HistoryRailProps = {
  reports: ReportIndexItem[];
  activeDate: string;
  onChange: (date: string) => void;
};

export function HistoryRail({ reports, activeDate, onChange }: HistoryRailProps) {
  return (
    <aside className="card p-4 lg:sticky lg:top-5 lg:h-[calc(100vh-40px)] lg:overflow-auto">
      <div className="flex items-center gap-2">
        <div className="rounded-md bg-ink p-2 text-white">
          <History size={17} />
        </div>
        <div>
          <p className="label">History</p>
          <h2 className="text-base font-semibold text-ink">最近 7 天日报</h2>
        </div>
      </div>
      <div className="mt-5 space-y-2">
        {reports.map((report) => {
          const active = report.date === activeDate;
          return (
            <button
              key={report.date}
              type="button"
              onClick={() => onChange(report.date)}
              className={`focus-ring w-full rounded-lg border px-3 py-3 text-left transition ${
                active
                  ? "border-ink bg-ink text-white shadow-tight"
                  : "border-line bg-white text-zinc-700 hover:border-zinc-300"
              }`}
            >
              <span className="flex items-start justify-between gap-3">
                <span>
                  <span className={`flex items-center gap-2 text-xs ${active ? "text-zinc-200" : "text-zinc-500"}`}>
                    <CalendarDays size={14} />
                    {report.date}
                  </span>
                  <span className="mt-1 block text-sm font-semibold">{report.title.replace(`${report.date} `, "")}</span>
                  <span className={`mt-1 block text-xs ${active ? "text-zinc-300" : "text-zinc-500"}`}>
                    {report.newsCount} 新闻 / {report.jobsCount} 岗位 / {report.trendsCount} 趋势
                  </span>
                </span>
                <ChevronRight size={16} />
              </span>
            </button>
          );
        })}
      </div>
    </aside>
  );
}
