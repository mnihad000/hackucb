import { forwardRef, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  motion,
  useScroll,
  useSpring,
  useTransform,
  type MotionValue,
  type Variants,
} from "framer-motion";
import Header from "../components/layout/Header";
import { ApiError, createInvestigation } from "../lib/api";
import { createInvestigationHref, radarTopics } from "../lib/demoData";
import type { RadarTopic } from "../types/rhetoriq";

const EASE_OUT = [0.16, 1, 0.3, 1] as const;

export default function LandingPage() {
  const streamRef = useRef<HTMLDivElement>(null);
  const promptRef = useRef<HTMLDivElement>(null);

  // The line "draws" downward as the stream scrolls through the viewport.
  const { scrollYProgress } = useScroll({
    target: streamRef,
    offset: ["start 0.65", "end 0.85"],
  });
  const draw = useSpring(scrollYProgress, {
    stiffness: 90,
    damping: 24,
    restDelta: 0.001,
  });

  function scrollToStream() {
    streamRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <main className="relative overflow-x-clip">
      <Header />
      <Hero onGetStarted={scrollToStream} />

      {/* ── Narrative spine: the line that runs through every trending story ── */}
      <section ref={streamRef} className="relative px-4 pb-4 pt-10 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <SpineHeading />

          <div className="relative mt-14">
            {/* Static track */}
            <div
              aria-hidden="true"
              className="absolute bottom-0 left-1/2 top-0 w-px -translate-x-1/2 bg-[var(--border)]"
            />
            {/* Drawn line (follows scroll) */}
            <motion.div
              aria-hidden="true"
              className="absolute left-1/2 top-0 w-px -translate-x-1/2 origin-top bg-[var(--ink)]"
              style={{ bottom: 0, scaleY: draw }}
            />
            {/* Traveling node at the tip of the drawn line */}
            <TravelingNode progress={draw} />

            {/* Story rows */}
            <div className="relative">
              {radarTopics.map((topic, index) => (
                <StoryRow key={topic.id} topic={topic} index={index} />
              ))}
            </div>

            {/* Terminal node into the prompt */}
            <div
              aria-hidden="true"
              className="relative z-10 mx-auto flex h-10 w-10 -translate-y-2 items-center justify-center"
            >
              <span className="absolute h-3 w-3 rounded-full bg-[var(--ink)]" />
              <span className="absolute h-10 w-10 rounded-full border border-[var(--ink)] opacity-20" />
            </div>
          </div>

          {/* ── The line ends here: prompt to begin an investigation ── */}
          <PromptModule ref={promptRef} />
        </div>
      </section>
    </main>
  );
}

/* ════════════════════════════════════════════════════════════
   HERO
════════════════════════════════════════════════════════════ */

const wordRise: Variants = {
  hidden: { opacity: 0, y: "0.4em" },
  show: (i: number) => ({
    opacity: 1,
    y: "0em",
    transition: { delay: 0.15 + i * 0.08, duration: 0.7, ease: EASE_OUT },
  }),
};

function Hero({ onGetStarted }: { onGetStarted: () => void }) {
  const headline = ["Trace", "how", "political", "stories", "spread."];

  return (
    <section className="relative flex min-h-[88vh] flex-col items-center justify-center px-4 text-center sm:px-6">
      {/* Faint vertical seed of the spine, descending from the headline */}
      <motion.div
        aria-hidden="true"
        initial={{ scaleY: 0, opacity: 0 }}
        animate={{ scaleY: 1, opacity: 1 }}
        transition={{ delay: 0.9, duration: 1.1, ease: EASE_OUT }}
        className="absolute bottom-0 left-1/2 h-24 w-px origin-top -translate-x-1/2 bg-gradient-to-b from-transparent via-[var(--border)] to-[var(--ink)]"
      />

      <motion.p
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="eyebrow"
      >
        Source-grounded narrative intelligence
      </motion.p>

      <h1 className="mt-7 max-w-4xl text-5xl font-semibold leading-[0.98] tracking-[-0.05em] text-[var(--ink)] sm:text-6xl lg:text-7xl">
        {headline.map((word, i) => (
          <span key={word} className="inline-block overflow-hidden align-baseline">
            <motion.span
              custom={i}
              variants={wordRise}
              initial="hidden"
              animate="show"
              className="inline-block pr-[0.22em]"
            >
              {word}
            </motion.span>
          </span>
        ))}
      </h1>

      <motion.p
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7, duration: 0.7 }}
        className="mt-7 max-w-xl text-lg leading-8 text-[var(--muted)]"
      >
        Follow a single thread through every claim — how a narrative emerges,
        mutates, and gets challenged, with receipts at every turn.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.95, duration: 0.7 }}
        className="mt-10"
      >
        <button
          type="button"
          onClick={onGetStarted}
          className="group inline-flex items-center gap-3 rounded-full bg-[var(--ink)] px-7 py-3.5 text-sm font-semibold tracking-wide text-white transition hover:-translate-y-0.5 hover:shadow-[0_16px_40px_-18px_rgba(19,35,58,0.6)]"
        >
          Get started
          <motion.span
            aria-hidden="true"
            className="text-base"
            animate={{ y: [0, 4, 0] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
          >
            ↓
          </motion.span>
        </button>
      </motion.div>
    </section>
  );
}

/* ════════════════════════════════════════════════════════════
   SPINE — heading + traveling node
════════════════════════════════════════════════════════════ */

function SpineHeading() {
  return (
    <div className="text-center">
      <p className="eyebrow">Live narrative radar</p>
      <h2 className="section-title mt-5">Breaking into the conversation</h2>
      <p className="section-copy mx-auto mt-4">
        Each story sits on the thread. Follow it down to where you can start your
        own investigation.
      </p>
    </div>
  );
}

function TravelingNode({ progress }: { progress: MotionValue<number> }) {
  const top = useTransform(progress, [0, 1], ["0%", "100%"]);
  const opacity = useTransform(progress, [0, 0.02, 0.98, 1], [0, 1, 1, 0]);

  return (
    <motion.div
      aria-hidden="true"
      className="absolute left-1/2 z-20 -translate-x-1/2"
      style={{ top, opacity }}
    >
      <span className="absolute left-1/2 top-1/2 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--ink)]" />
      <motion.span
        className="absolute left-1/2 top-1/2 h-6 w-6 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--ink)]"
        animate={{ opacity: [0.18, 0, 0.18], scale: [0.8, 1.6, 0.8] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
      />
    </motion.div>
  );
}

/* ════════════════════════════════════════════════════════════
   STORY ROW — a "square" on the line that lights up on pass
════════════════════════════════════════════════════════════ */

function StoryRow({ topic, index }: { topic: RadarTopic; index: number }) {
  const navigate = useNavigate();
  const isLeft = index % 2 === 0;
  const label = String(index + 1).padStart(2, "0");

  return (
    <motion.div
      initial="dim"
      whileInView="lit"
      viewport={{ once: false, amount: 0.7, margin: "0px 0px -20% 0px" }}
      className="relative grid grid-cols-1 items-center gap-y-6 py-8 md:grid-cols-2 md:gap-x-20"
    >
      {/* Node where the card meets the line */}
      <motion.span
        aria-hidden="true"
        variants={{
          dim: { scale: 0.6, backgroundColor: "rgba(255,255,255,1)" },
          lit: { scale: 1, backgroundColor: "rgb(19,35,58)" },
        }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="absolute left-1/2 top-1/2 z-10 hidden h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[var(--ink)] md:block"
      />

      {/* Card — placed on alternating side; connector points to the line */}
      <div
        className={
          isLeft
            ? "md:col-start-1 md:pr-6 md:text-right"
            : "md:col-start-2 md:pl-6"
        }
      >
        <StoryCard topic={topic} label={label} alignRight={isLeft} navigate={navigate} />
      </div>
    </motion.div>
  );
}

function StoryCard({
  topic,
  label,
  alignRight,
  navigate,
}: {
  topic: RadarTopic;
  label: string;
  alignRight: boolean;
  navigate: ReturnType<typeof useNavigate>;
}) {
  return (
    <motion.button
      type="button"
      onClick={() => navigate(createInvestigationHref(topic.id))}
      variants={{
        dim: { opacity: 0.45, y: 18, borderColor: "rgba(23,44,71,0.12)" },
        lit: { opacity: 1, y: 0, borderColor: "rgba(23,44,71,0.28)" },
      }}
      transition={{ duration: 0.5, ease: EASE_OUT }}
      whileHover={{ y: -4 }}
      className="group block w-full rounded-[1.5rem] border bg-[var(--surface-strong)] p-6 text-left shadow-[0_24px_60px_-44px_rgba(19,35,58,0.5)] backdrop-blur-md transition-shadow hover:shadow-[0_34px_70px_-40px_rgba(19,35,58,0.5)]"
    >
      <div
        className={`flex items-baseline gap-3 ${alignRight ? "md:flex-row-reverse" : ""}`}
      >
        <span className="font-[Iowan_Old_Style,Palatino_Linotype,Book_Antiqua,Georgia,serif] text-sm font-semibold tracking-[0.1em] text-[var(--accent)]">
          {label}
        </span>
        <span className="text-[0.66rem] font-semibold uppercase tracking-[0.22em] text-[var(--muted)]">
          {topic.status}
        </span>
      </div>

      <h3 className="mt-3 text-2xl font-semibold tracking-[-0.03em] text-[var(--ink)]">
        {topic.title}
      </h3>
      <p className="mt-3 text-[0.95rem] leading-7 text-[var(--muted)]">
        {topic.summary}
      </p>

      <div
        className={`mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm ${
          alignRight ? "md:justify-end" : ""
        }`}
      >
        <Meta label="Spike" value={topic.spike} emphasized />
        <Meta label="Sources" value={String(topic.sourceCount)} />
        <Meta label="Confidence" value={topic.confidence} />
      </div>

      <span
        className={`mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-[var(--ink)] transition-colors group-hover:text-[var(--accent)] ${
          alignRight ? "md:flex-row-reverse" : ""
        }`}
      >
        Investigate
        <span
          aria-hidden="true"
          className="transition-transform group-hover:translate-x-1"
        >
          →
        </span>
      </span>
    </motion.button>
  );
}

function Meta({
  label,
  value,
  emphasized,
}: {
  label: string;
  value: string;
  emphasized?: boolean;
}) {
  return (
    <span className="inline-flex items-baseline gap-1.5">
      <span className="text-[var(--muted)]">{label}</span>
      <span
        className={`font-semibold ${emphasized ? "text-[var(--accent)]" : "text-[var(--ink)]"}`}
      >
        {value}
      </span>
    </span>
  );
}

/* ════════════════════════════════════════════════════════════
   PROMPT — where the thread terminates
════════════════════════════════════════════════════════════ */

const PromptModule = forwardRef<HTMLDivElement>(function PromptModule(_props, ref) {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      inputRef.current?.focus();
      return;
    }
    setErrorMessage(null);
    setIsSubmitting(true);
    try {
      const response = await createInvestigation(trimmed);
      navigate(createInvestigationHref(response.investigation_id, trimmed));
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError
          ? error.message
          : "Unable to start the investigation right now.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.4 }}
      transition={{ duration: 0.6, ease: EASE_OUT }}
      className="mx-auto mt-2 max-w-2xl text-center"
    >
      <p className="eyebrow">The thread ends with you</p>
      <h2 className="mt-5 text-4xl font-semibold tracking-[-0.04em] text-[var(--ink)] sm:text-5xl">
        Start your own investigation.
      </h2>
      <p className="mx-auto mt-4 max-w-lg text-base leading-7 text-[var(--muted)]">
        Paste a headline, claim, article URL, or topic. RhetoriQ traces it back
        to the source.
      </p>

      <form onSubmit={handleSubmit} className="mt-8">
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Paste a headline, claim, article URL, or topic…"
            disabled={isSubmitting}
            className="w-full rounded-full border border-[var(--border)] bg-white px-6 py-4 text-base text-[var(--ink)] shadow-[0_18px_40px_-30px_rgba(17,35,59,0.4)] outline-none transition placeholder:text-[color:rgba(90,104,125,0.8)] focus:border-[var(--accent)] focus:ring-4 focus:ring-[rgba(124,144,172,0.16)]"
          />
          <button
            type="submit"
            disabled={isSubmitting}
            className="shrink-0 rounded-full bg-[var(--ink)] px-7 py-4 text-base font-semibold text-white transition hover:-translate-y-0.5 hover:shadow-[0_18px_44px_-20px_rgba(19,35,58,0.6)] disabled:opacity-60"
          >
            {isSubmitting ? "Starting…" : "Investigate"}
          </button>
        </div>
      </form>

      {errorMessage ? (
        <p className="mx-auto mt-4 max-w-lg rounded-[1rem] border border-[rgba(146,71,71,0.18)] bg-[rgba(255,244,244,0.92)] px-4 py-3 text-sm leading-6 text-[rgb(130,50,50)]">
          {errorMessage}
        </p>
      ) : null}

      <p className="mt-16 pb-10 text-xs font-medium uppercase tracking-[0.24em] text-[var(--muted)]">
        Source-grounded · Nonpartisan by design · Built for human review
      </p>
    </motion.div>
  );
});
