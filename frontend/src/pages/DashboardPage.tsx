import { startTransition, useEffect, useState } from "react";
import Hero from "../components/dashboard/Hero";
import NarrativeRadar from "../components/dashboard/NarrativeRadar";
import RecentInvestigations from "../components/dashboard/RecentInvestigations";
import TrustStrip from "../components/dashboard/TrustStrip";
import Header from "../components/layout/Header";
import { ApiError, getTrendingFeed } from "../lib/api";
import { examplePrompts, recentInvestigations } from "../lib/demoData";
import type { LiveTrendingFeed } from "../types/rhetoriq";

export default function DashboardPage() {
  const [feed, setFeed] = useState<LiveTrendingFeed | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadFeed() {
      try {
        const nextFeed = await getTrendingFeed();
        if (cancelled) {
          return;
        }
        startTransition(() => {
          setFeed(nextFeed);
          setErrorMessage(null);
        });
      } catch (error) {
        if (cancelled) {
          return;
        }
        setErrorMessage(
          error instanceof ApiError
            ? error.message
            : "Unable to load the live hot-topics feed.",
        );
      }
    }

    void loadFeed();
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
        <NarrativeRadar feed={feed} errorMessage={errorMessage} />
        <RecentInvestigations investigations={recentInvestigations} />
        <TrustStrip />
      </div>
    </main>
  );
}
