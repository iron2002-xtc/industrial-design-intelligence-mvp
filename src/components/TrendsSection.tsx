import { ExternalLink, Layers } from "lucide-react";
import type { TrendItem } from "../types/report";

type TrendsSectionProps = {
  trends: TrendItem[];
};

export function TrendsSection({ trends }: TrendsSectionProps) {
  return (
    <section className="card p-4 sm:p-5" id="trends">
      <div className="mb-5">
        <p className="label">Trend Board</p>
        <h2 className="mt-2 text-xl font-semibold text-ink">趋势区块</h2>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
          按 AI硬件、3C、清洁电器、机器人、家电、CMF、AI工具和作品集案例分组，方便后续扩展为历史趋势库。
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {trends.map((trend) => (
          <article key={trend.id} className="rounded-lg border border-line bg-white p-4">
            <div className="flex items-center justify-between gap-3">
              <span className="inline-flex items-center gap-2 rounded-md bg-zinc-100 px-2 py-1 text-xs font-semibold text-zinc-600">
                <Layers size={13} />
                {trend.category}
              </span>
            </div>
            <h3 className="mt-3 text-base font-semibold leading-snug text-ink">{trend.title}</h3>
            <p className="mt-3 text-sm leading-6 text-zinc-600">{trend.trendSummary}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {trend.relatedCases.map((item) => (
                <span key={item} className="rounded-md bg-signal/10 px-2 py-1 text-xs font-medium text-signal">
                  {item}
                </span>
              ))}
            </div>
            <p className="mt-4 text-sm leading-6 text-zinc-500">启发：{trend.designInspiration}</p>
            <a
              href={trend.url}
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
    </section>
  );
}
