import type { ReactNode } from "react";

type MetricCardProps = {
  label: string;
  value: number | string;
  helper: string;
  icon: ReactNode;
  tone?: "green" | "copper" | "plum" | "ink";
};

const toneMap = {
  green: "bg-signal/10 text-signal",
  copper: "bg-copper/10 text-copper",
  plum: "bg-plum/10 text-plum",
  ink: "bg-zinc-900 text-white",
};

export function MetricCard({ label, value, helper, icon, tone = "green" }: MetricCardProps) {
  return (
    <article className="subtle-card p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="label">{label}</p>
          <p className="mt-2 text-3xl font-semibold text-ink">{value}</p>
        </div>
        <div className={`rounded-md p-2.5 ${toneMap[tone]}`}>{icon}</div>
      </div>
      <p className="mt-3 text-sm leading-6 text-zinc-500">{helper}</p>
    </article>
  );
}
