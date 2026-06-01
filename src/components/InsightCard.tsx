import { ExternalLink } from "lucide-react";
import type { NewsItem } from "../types/report";

type InsightCardProps = {
  item: NewsItem;
  compact?: boolean;
};

export function InsightCard({ item, compact = false }: InsightCardProps) {
  return (
    <article className="rounded-lg border border-line bg-white p-4 transition hover:-translate-y-0.5 hover:shadow-tight">
      <div className="flex items-start justify-between gap-3">
        <div>
          <span className="rounded-md bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-600">
            {item.category}
          </span>
          <h3 className="mt-3 text-base font-semibold leading-snug text-ink">{item.title}</h3>
        </div>
        <span className="shrink-0 rounded-md bg-signal/10 px-2 py-1 text-xs font-semibold text-signal">
          {item.importanceScore}
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-zinc-600">{item.summary}</p>
      {!compact && <p className="mt-3 text-sm leading-6 text-zinc-500">设计启发：{item.designInsight}</p>}
      <a
        className="focus-ring mt-4 inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium text-zinc-700 transition hover:border-zinc-300 hover:bg-zinc-50"
        href={item.url}
        target="_blank"
        rel="noreferrer"
      >
        原始链接
        <ExternalLink size={15} />
      </a>
    </article>
  );
}
