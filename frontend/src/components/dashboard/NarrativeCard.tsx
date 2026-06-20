import { Link } from "react-router-dom";
import { createInvestigationHref } from "../../lib/demoData";
import type { RadarTopic } from "../../types/rhetoriq";

type NarrativeCardProps = {
  topic: RadarTopic;
};

export default function NarrativeCard({ topic }: NarrativeCardProps) {
  return (
    <article className="surface-card group flex h-full flex-col p-6 transition duration-300 hover:-translate-y-1.5 hover:border-[var(--accent)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="eyebrow">{topic.status}</p>
          <h3 className="mt-4 text-2xl font-semibold tracking-[-0.04em] text-[var(--ink)]">
            {topic.title}
          </h3>
        </div>
        <span className="rounded-full bg-[rgba(124,144,172,0.12)] px-3 py-1 text-sm font-semibold text-[var(--accent)]">
          {topic.confidence}
        </span>
      </div>

      <p className="mt-4 flex-1 text-base leading-7 text-[var(--muted)]">{topic.summary}</p>

      <dl className="mt-6 grid grid-cols-2 gap-4 border-t border-[var(--border)] pt-5 text-sm">
        <div>
          <dt className="text-[var(--muted)]">Spike</dt>
          <dd className="mt-1 text-lg font-semibold text-[var(--ink)]">{topic.spike}</dd>
        </div>
        <div>
          <dt className="text-[var(--muted)]">Sources</dt>
          <dd className="mt-1 text-lg font-semibold text-[var(--ink)]">{topic.sourceCount}</dd>
        </div>
      </dl>

      <div className="mt-6 space-y-3 text-sm text-[var(--muted)]">
        <p>{topic.firstObserved}</p>
        <p>
          <span className="font-semibold text-[var(--ink)]">Source mix:</span> {topic.sourceMix}
        </p>
      </div>

      <Link
        to={createInvestigationHref(topic.id)}
        className="mt-6 inline-flex items-center justify-between rounded-[1.1rem] border border-[var(--border)] bg-white px-4 py-3 text-sm font-semibold text-[var(--ink)] transition hover:border-[var(--accent)] hover:text-[var(--accent)]"
      >
        Investigate
        <span aria-hidden="true" className="transition group-hover:translate-x-1">
          →
        </span>
      </Link>
    </article>
  );
}
