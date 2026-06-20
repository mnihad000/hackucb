import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createInvestigationHref } from "../../lib/demoData";
import { ApiError, createInvestigation } from "../../lib/api";
import type { ExamplePrompt } from "../../types/rhetoriq";

type AskRhetoriQProps = {
  prompts: ExamplePrompt[];
};

export default function AskRhetoriQ({ prompts }: AskRhetoriQProps) {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [query, setQuery] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      inputRef.current?.focus();
      return;
    }

    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const response = await createInvestigation(trimmedQuery);
      navigate(createInvestigationHref(response.investigation_id, trimmedQuery));
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError
          ? error.message
          : "Unable to start the live investigation right now.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function applyPrompt(prompt: ExamplePrompt) {
    setQuery(prompt.query);
    setErrorMessage(null);
    inputRef.current?.focus();
  }

  return (
    <div className="surface-card relative overflow-hidden p-6 sm:p-7">
      <div className="absolute inset-x-0 top-0 h-24 bg-[linear-gradient(135deg,rgba(197,210,226,0.26),rgba(197,210,226,0))]" />
      <div className="relative">
        <p className="eyebrow">Ask RhetoriQ</p>
        <h2 className="mt-4 text-3xl font-semibold tracking-[-0.03em] text-[var(--ink)]">
          Start with a political story, claim, phrase, or issue.
        </h2>
        <p className="mt-3 text-base leading-7 text-[var(--muted)]">
          This now creates a live investigation plan, then the investigation page runs
          retrieval, timeline, counter-narrative, analyst, and report steps from the
          backend.
        </p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="rhetoriq-query">
            Ask about any political story, claim, phrase, or issue
          </label>
          <input
            id="rhetoriq-query"
            ref={inputRef}
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Ask about any political story, claim, phrase, or issue..."
            className="w-full rounded-[1.4rem] border border-[var(--border)] bg-white px-5 py-4 text-lg text-[var(--ink)] shadow-[0_18px_40px_-30px_rgba(17,35,59,0.35)] outline-none transition placeholder:text-[color:rgba(90,104,125,0.85)] focus:border-[var(--accent)] focus:ring-4 focus:ring-[rgba(124,144,172,0.14)]"
            disabled={isSubmitting}
          />
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex w-full items-center justify-center rounded-[1.2rem] bg-[var(--ink)] px-5 py-4 text-base font-semibold text-white transition hover:-translate-y-0.5 hover:bg-[var(--accent)] focus:outline-none focus:ring-4 focus:ring-[rgba(124,144,172,0.18)]"
          >
            {isSubmitting ? "Starting investigation..." : "Investigate"}
          </button>
        </form>
        {errorMessage ? (
          <p className="mt-4 rounded-[1rem] border border-[rgba(146,71,71,0.18)] bg-[rgba(255,244,244,0.92)] px-4 py-3 text-sm leading-6 text-[rgb(130,50,50)]">
            {errorMessage}
          </p>
        ) : null}

        <div className="mt-6">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">
            Example prompts
          </p>
          <div className="mt-3 flex flex-wrap gap-2.5">
            {prompts.map((prompt) => (
              <button
                key={prompt.id}
                type="button"
                onClick={() => applyPrompt(prompt)}
                className="rounded-full border border-[var(--border)] bg-white/80 px-4 py-2 text-sm font-medium text-[var(--ink)] transition hover:-translate-y-0.5 hover:border-[var(--accent)] hover:text-[var(--accent)] focus:outline-none focus:ring-4 focus:ring-[rgba(124,144,172,0.12)]"
              >
                {prompt.query}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
