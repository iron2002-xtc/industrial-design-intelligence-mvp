import type { ReactNode } from "react";

type SectionCardProps = {
  eyebrow: string;
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
};

export function SectionCard({ eyebrow, title, description, action, children }: SectionCardProps) {
  return (
    <section className="card p-4 sm:p-5">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="label">{eyebrow}</p>
          <h2 className="mt-2 text-xl font-semibold tracking-normal text-ink">{title}</h2>
          {description && <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">{description}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
