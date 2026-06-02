import { BriefcaseBusiness, ExternalLink, Filter, MapPin, SlidersHorizontal } from "lucide-react";
import { useMemo, useState } from "react";
import { cities, directions } from "../data/filterOptions";
import { textMatches } from "../lib/search";
import type { JobItem } from "../types/report";

type JobsSectionProps = {
  jobs: JobItem[];
  searchQuery: string;
};

const scoreOptions = [
  { label: "全部", value: 0 },
  { label: "90+", value: 90 },
  { label: "80+", value: 80 },
  { label: "70+", value: 70 },
];

function SelectField({
  label,
  value,
  onChange,
  children,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-2 flex items-center gap-2 text-xs font-semibold text-zinc-500">
        <SlidersHorizontal size={14} />
        {label}
      </span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="focus-ring w-full rounded-md border border-line bg-white px-3 py-2.5 text-sm font-medium text-zinc-700"
      >
        {children}
      </select>
    </label>
  );
}

export function JobsSection({ jobs, searchQuery }: JobsSectionProps) {
  const [city, setCity] = useState("全部");
  const [direction, setDirection] = useState("全部");
  const [score, setScore] = useState("0");

  const filteredJobs = useMemo(() => {
    const minScore = Number(score);
    return jobs
      .filter((job) => city === "全部" || job.city === city)
      .filter((job) => direction === "全部" || job.direction === direction)
      .filter((job) => job.matchScore >= minScore)
      .filter((job) =>
        textMatches(
          [
            job.company,
            job.title,
            job.city,
            job.direction,
            job.experience,
            job.reason,
            job.jobType ?? "",
            job.requirementsSummary ?? "",
            (job.tags ?? job.keywords ?? []).join(" "),
          ],
          searchQuery,
        ),
      )
      .sort((a, b) => b.matchScore - a.matchScore);
  }, [city, direction, jobs, score, searchQuery]);

  return (
    <section className="card p-4 sm:p-5" id="jobs">
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="label">Recruiting Radar</p>
          <h2 className="mt-2 text-xl font-semibold text-ink">今日高匹配工业设计岗位</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
            用城市、方向和匹配度先筛出值得认真准备作品集投递的岗位，优先看官网来源和应届/初级可投机会。
          </p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-md bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-600">
          <Filter size={16} />
          {filteredJobs.length} / {jobs.length}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <SelectField label="城市筛选" value={city} onChange={setCity}>
          <option value="全部">全部</option>
          {cities.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </SelectField>
        <SelectField label="方向筛选" value={direction} onChange={setDirection}>
          <option value="全部">全部</option>
          {directions.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </SelectField>
        <SelectField label="匹配度筛选" value={score} onChange={setScore}>
          {scoreOptions.map((item) => (
            <option key={item.label} value={item.value}>
              {item.label}
            </option>
          ))}
        </SelectField>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-2">
        {filteredJobs.map((job) => (
          <article key={job.id} className="rounded-lg border border-line bg-white p-4 transition hover:-translate-y-0.5 hover:shadow-tight">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-zinc-500">{job.company}</p>
                <h3 className="mt-1 text-lg font-semibold leading-snug text-ink">{job.title}</h3>
              </div>
              <div className="rounded-md bg-ink px-2.5 py-2 text-center text-white">
                <span className="block text-lg font-semibold leading-none">{job.matchScore}</span>
                <span className="mt-1 block text-[10px] uppercase text-zinc-300">match</span>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="inline-flex items-center gap-1 rounded-md bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-600">
                <MapPin size={13} />
                {job.city}
              </span>
              <span className="inline-flex items-center gap-1 rounded-md bg-signal/10 px-2 py-1 text-xs font-medium text-signal">
                <BriefcaseBusiness size={13} />
                {job.direction}
              </span>
              <span className="rounded-md bg-copper/10 px-2 py-1 text-xs font-medium text-copper">{job.experience}</span>
              {job.jobType && (
                <span className="rounded-md bg-plum/10 px-2 py-1 text-xs font-medium text-plum">{job.jobType}</span>
              )}
              {typeof job.sourceQualityScore === "number" && job.sourceQualityScore >= 85 && (
                <span className="rounded-md bg-ink px-2 py-1 text-xs font-medium text-white">高可信</span>
              )}
            </div>
            <p className="mt-4 text-sm leading-6 text-zinc-600">{job.reason}</p>
            {job.requirementsSummary && (
              <p className="mt-2 text-sm leading-6 text-zinc-500">要求概览：{job.requirementsSummary}</p>
            )}
            {!!(job.tags ?? job.keywords)?.length && (
              <div className="mt-3 flex flex-wrap gap-2">
                {(job.tags ?? job.keywords ?? []).slice(0, 5).map((tag) => (
                  <span key={tag} className="rounded-md bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-500">
                    {tag}
                  </span>
                ))}
              </div>
            )}
            <a
              href={job.url}
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

      {filteredJobs.length === 0 && (
        <div className="mt-5 rounded-lg border border-dashed border-line bg-zinc-50 px-4 py-8 text-center text-sm text-zinc-500">
          没有匹配的岗位，换一个城市、方向或搜索词试试。
        </div>
      )}
    </section>
  );
}
