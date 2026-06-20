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
      <Hero prompts={examplePrompts} />
      <NarrativeRadar feed={feed} errorMessage={errorMessage} />
      <RecentInvestigations investigations={recentInvestigations} />
      <TrustStrip />
    </main>
  );
}
