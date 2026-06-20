import AskRhetoriQ from "./AskRhetoriQ";
import type { ExamplePrompt } from "../../types/rhetoriq";

type HeroProps = {
  prompts: ExamplePrompt[];
};

export default function Hero({ prompts }: HeroProps) {
  return (
    <section className="px-4 pb-8 pt-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <div className="surface-card page-enter relative overflow-hidden px-6 py-8 sm:px-8 sm:py-10 lg:px-12 lg:py-14">
          <div className="absolute -left-20 top-14 h-52 w-52 rounded-full bg-[rgba(193,208,227,0.22)] blur-3xl" />
          <div className="absolute bottom-0 right-0 h-72 w-72 rounded-full bg-[rgba(228,235,244,0.34)] blur-3xl" />

          <div className="relative grid gap-10 lg:grid-cols-[1.08fr_0.92fr] lg:items-center">
            <div className="max-w-3xl">
              <p className="eyebrow">Source-grounded narrative intelligence</p>
              <h1 className="mt-5 text-5xl font-semibold leading-[0.96] tracking-[-0.06em] text-[var(--ink)] sm:text-6xl lg:text-7xl">
                Trace how political stories spread.
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-[var(--muted)] sm:text-xl">
                RhetoriQ investigates political stories, maps how the narrative evolves,
                and gives every major claim a path back to evidence.
              </p>

              <div className="mt-7 flex flex-wrap gap-3">
                <span className="data-pill">Clickable receipts</span>
                <span className="data-pill">Counter-narratives</span>
                <span className="data-pill">Human review recommended</span>
              </div>

              <p className="mt-8 max-w-xl text-sm font-medium uppercase tracking-[0.22em] text-[var(--muted)]">
                Source-grounded. Nonpartisan by design. Built for human review.
              </p>
            </div>

            <AskRhetoriQ prompts={prompts} />
          </div>
        </div>
      </div>
    </section>
  );
}
