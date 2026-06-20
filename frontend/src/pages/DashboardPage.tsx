import Hero from "../components/dashboard/Hero";
import NarrativeRadar from "../components/dashboard/NarrativeRadar";
import RecentInvestigations from "../components/dashboard/RecentInvestigations";
import TrustStrip from "../components/dashboard/TrustStrip";
import Header from "../components/layout/Header";
import {
  examplePrompts,
  radarTopics,
  recentInvestigations,
} from "../lib/demoData";

export default function DashboardPage() {
  return (
    <main>
      <Header />
      <Hero prompts={examplePrompts} />
      <NarrativeRadar topics={radarTopics} />
      <RecentInvestigations investigations={recentInvestigations} />
      <TrustStrip />
    </main>
  );
}
