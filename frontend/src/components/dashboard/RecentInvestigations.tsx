import { Link } from "react-router-dom";
import { createInvestigationHref } from "../../lib/demoData";
import Section from "../layout/Section";
import type { RecentInvestigation } from "../../types/rhetoriq";

type RecentInvestigationsProps = {
  investigations: RecentInvestigation[];
};

export default function RecentInvestigations({
  investigations,
}: RecentInvestigationsProps) {
  return (
    <Section
      eyebrow="Recent Investigations"
      title="Open a prepared investigation flow."
      description="These seeded stories act as reliable jump points for demos, screenshots, and the first backend integration pass."
      className="pt-16"
    >
      <div className="grid gap-4 lg:grid-cols-3">
        {investigations.map((investigation) => (
          <Link
            key={investigation.id}
            to={createInvestigationHref(investigation.id)}
            className="surface-card group flex h-full flex-col gap-5 p-6 transition hover:-translate-y-1 hover:border-[var(--accent)]"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="eyebrow">{investigation.focus}</p>
                <h3 className="mt-4 text-2xl font-semibold tracking-[-0.03em] text-[var(--ink)]">
                  {investigation.title}
                </h3>
              </div>
              <span className="rounded-full border border-[var(--border)] px-3 py-1 text-sm font-semibold text-[var(--muted)]">
                {investigation.receiptCount} receipts
              </span>
            </div>

            <p className="flex-1 text-base leading-7 text-[var(--muted)]">
              {investigation.summary}
            </p>

            <div className="flex items-center justify-between text-sm text-[var(--muted)]">
              <span>{investigation.updatedAt}</span>
              <span
                aria-hidden="true"
                className="text-base text-[var(--accent)] transition group-hover:translate-x-1"
              >
                →
              </span>
            </div>
          </Link>
        ))}
      </div>
    </Section>
  );
}
