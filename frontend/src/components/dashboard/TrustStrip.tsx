export default function TrustStrip() {
  return (
    <section className="px-4 pb-20 pt-16 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <div className="surface-card overflow-hidden px-6 py-6 sm:px-8 sm:py-7">
          <div className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr] lg:items-center">
            <div>
              <p className="eyebrow">Trust framing</p>
              <p className="mt-4 text-lg leading-8 text-[var(--ink)] sm:text-xl">
                RhetoriQ does not assign truth scores or bias scores. It traces first
                observed sources, maps spread patterns, surfaces counter-narratives, and
                gives each finding a path back to evidence for human review.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
              <div className="rounded-[1.3rem] border border-[var(--border)] bg-white/75 px-4 py-4 text-sm font-semibold text-[var(--ink)]">
                First observed in our dataset
              </div>
              <div className="rounded-[1.3rem] border border-[var(--border)] bg-white/75 px-4 py-4 text-sm font-semibold text-[var(--ink)]">
                Signals consistent with evidence
              </div>
              <div className="rounded-[1.3rem] border border-[var(--border)] bg-white/75 px-4 py-4 text-sm font-semibold text-[var(--ink)]">
                Human review recommended
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
