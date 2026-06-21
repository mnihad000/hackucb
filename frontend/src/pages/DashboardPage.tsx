import { startTransition, useEffect, useState } from "react";
import Hero from "../components/dashboard/Hero";
import NarrativeRadar from "../components/dashboard/NarrativeRadar";
import RecentInvestigations from "../components/dashboard/RecentInvestigations";
import TrustStrip from "../components/dashboard/TrustStrip";
import Header from "../components/layout/Header";
import { ApiError, getRecentInvestigations, getTrendingFeed } from "../lib/api";
import { examplePrompts } from "../lib/demoData";
import type {
  LiveRecentInvestigationSummary,
  LiveTrendingFeed,
} from "../types/rhetoriq";

export default function DashboardPage() {
  const [feed, setFeed] = useState<LiveTrendingFeed | null>(null);
  const [feedErrorMessage, setFeedErrorMessage] = useState<string | null>(null);
  const [recentInvestigations, setRecentInvestigations] = useState<
    LiveRecentInvestigationSummary[] | null
  >(null);
  const [recentErrorMessage, setRecentErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      const [feedResult, recentResult] = await Promise.allSettled([
        getTrendingFeed(),
        getRecentInvestigations(),
      ]);

      if (cancelled) {
        return;
      }

      if (feedResult.status === "fulfilled") {
        startTransition(() => {
          setFeed(feedResult.value);
          setFeedErrorMessage(null);
        });
      } else {
        const error = feedResult.reason;
        setFeedErrorMessage(
          error instanceof ApiError
            ? error.message
            : "Unable to load the live hot-topics feed.",
        );
      }

      if (recentResult.status === "fulfilled") {
        startTransition(() => {
          setRecentInvestigations(recentResult.value);
          setRecentErrorMessage(null);
        });
      } else {
        const error = recentResult.reason;
        setRecentErrorMessage(
          error instanceof ApiError
            ? error.message
            : "Unable to load recent live investigations.",
        );
      }
    }

    void loadDashboard();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main>
      <Header />

      {/* Signal thread — thin vertical line with traveling glow, runs behind all sections */}
      <div className="relative">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute bottom-0 top-0 w-px"
          style={{
            left: "max(1.25rem, calc(50% - 39.5rem))",
            background:
              "linear-gradient(180deg, transparent 0%, rgba(23,44,71,0.22) 6%, rgba(23,44,71,0.22) 94%, transparent 100%)",
          }}
        >
          <div
            className="absolute h-24 w-full"
            style={{
              background:
                "linear-gradient(180deg, transparent 0%, var(--accent) 50%, transparent 100%)",
              opacity: 0.8,
              animation: "signal-travel 5s cubic-bezier(0.4, 0, 0.6, 1) infinite",
            }}
          />
        </div>

        <Hero prompts={examplePrompts} />
        <NarrativeRadar feed={feed} errorMessage={feedErrorMessage} />
        <RecentInvestigations
          investigations={recentInvestigations}
          errorMessage={recentErrorMessage}
        />
        <TrustStrip />
      </div>
    </main>
  );
}
